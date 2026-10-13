"""Unit and integration tests for authentication and RBAC."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_user(client: AsyncClient) -> None:
    """Test standard shopper registration and subsequent login."""
    unique_email = f"shopper_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPassword123!"

    # 1. Register
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": password,
            "full_name": "Test Shopper",
            "role": "user",
        },
    )
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == unique_email
    assert data["user"]["role"] == "user"
    assert "refresh_token" in reg_resp.cookies

    access_token = data["access_token"]

    # 2. Access /me with valid token
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == unique_email

    # 3. Login with credentials
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data


@pytest.mark.asyncio
async def test_duplicate_registration_fails(client: AsyncClient) -> None:
    """Test duplicate registration produces RFC 7807 409 Conflict."""
    email = f"duplicate_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "Password123!",
        "full_name": "First User",
        "role": "user",
    }

    resp1 = await client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409
    error = resp2.json()
    assert error["code"] == "USER_ALREADY_EXISTS"
    assert error["status"] == 409


@pytest.mark.asyncio
async def test_invalid_credentials_fails(client: AsyncClient) -> None:
    """Test invalid credentials rejection."""
    email = f"invalid_{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "CorrectPassword123!",
            "full_name": "Valid User",
            "role": "user",
        },
    )

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword123!"},
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_reuse_detection(client: AsyncClient) -> None:
    """Test rotation and security revocation when a reused token is presented."""
    email = f"rotation_{uuid.uuid4().hex[:8]}@example.com"
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Rotation User",
            "role": "user",
        },
    )
    assert reg_resp.status_code == 201
    initial_refresh = reg_resp.cookies.get("refresh_token")
    assert initial_refresh is not None

    # Step 1: Valid rotation using cookie
    rotate_resp = await client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": initial_refresh},
    )
    assert rotate_resp.status_code == 200
    new_refresh = rotate_resp.cookies.get("refresh_token")
    assert new_refresh is not None
    assert new_refresh != initial_refresh

    # Step 2: Attempt to reuse the old, already-rotated token -> should trigger reuse detection
    reused_resp = await client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": initial_refresh},
    )
    assert reused_resp.status_code == 401
    assert reused_resp.json()["code"] == "TOKEN_REUSE_DETECTED"

    # Step 3: Verify the new token has ALSO been invalidated due to reuse detection
    invalidated_resp = await client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": new_refresh},
    )
    assert invalidated_resp.status_code == 401


@pytest.mark.asyncio
async def test_unauthorized_access_to_protected_endpoint(client: AsyncClient) -> None:
    """Test that requests without valid Authorization header return 401."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert resp.json()["code"] == "MISSING_TOKEN"


@pytest.mark.asyncio
async def test_merchant_registration_and_role_distinction(client: AsyncClient) -> None:
    """Test merchant account creation and role representation."""
    email = f"merchant_{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "MerchantPassword123!",
            "full_name": "Store Manager Maria",
            "role": "merchant",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["user"]["role"] == "merchant"


@pytest.mark.asyncio
async def test_role_based_access_control_guard(client: AsyncClient) -> None:
    """Verify that a shopper user cannot access merchant-only dependencies."""
    # Register standard shopper
    shopper_email = f"shopper_rbac_{uuid.uuid4().hex[:8]}@example.com"
    shopper_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": shopper_email,
            "password": "ShopperPassword123!",
            "full_name": "Shopper Jane",
            "role": "user",
        },
    )
    assert shopper_resp.status_code == 201
    shopper_token = shopper_resp.json()["access_token"]

    # Shopper attempts to hit merchant route -> 403 Forbidden
    forbidden_resp = await client.get(
        "/api/v1/auth/merchant-check",
        headers={"Authorization": f"Bearer {shopper_token}"},
    )
    assert forbidden_resp.status_code == 403
    assert forbidden_resp.json()["code"] == "ROLE_NOT_AUTHORIZED"

    # Register merchant
    merchant_email = f"merchant_rbac_{uuid.uuid4().hex[:8]}@example.com"
    merchant_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": merchant_email,
            "password": "MerchantPassword123!",
            "full_name": "Merchant Bob",
            "role": "merchant",
        },
    )
    assert merchant_resp.status_code == 201
    merchant_token = merchant_resp.json()["access_token"]

    # Merchant hits merchant route -> 200 OK
    allowed_resp = await client.get(
        "/api/v1/auth/merchant-check",
        headers={"Authorization": f"Bearer {merchant_token}"},
    )
    assert allowed_resp.status_code == 200
    assert allowed_resp.json()["status"] == "ok"
