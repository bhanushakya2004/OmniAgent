"""Unified Principal domain model representing authenticated users or anonymous guests."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

from omnimission.models.user import User


@dataclass
class Principal:
    """Represents the calling identity (authenticated user, merchant, or anonymous guest)."""

    principal_type: Literal["guest", "user", "merchant"] = "guest"
    user_id: uuid.UUID | None = None
    guest_session_id: uuid.UUID | None = None
    session_token: str | None = None
    email: str | None = None
    role: str | None = None
    user: User | None = None

    @classmethod
    def create_guest(cls, guest_session_id: uuid.UUID | None = None) -> Principal:
        """Factory for anonymous guest principal."""
        return cls(
            principal_type="guest",
            guest_session_id=guest_session_id or uuid.uuid4(),
            role="user",
        )

    @classmethod
    def create_user(
        cls,
        user_id: uuid.UUID,
        email: str | None = None,
        role: str = "user",
        user: User | None = None,
    ) -> Principal:
        """Factory for authenticated shopper user principal."""
        return cls(
            principal_type="user",
            user_id=user_id,
            email=email,
            role=role,
            user=user,
        )

    @classmethod
    def create_merchant(
        cls,
        user_id: uuid.UUID,
        email: str | None = None,
        user: User | None = None,
    ) -> Principal:
        """Factory for merchant principal."""
        return cls(
            principal_type="merchant",
            user_id=user_id,
            email=email,
            role="merchant",
            user=user,
        )

    @property
    def is_authenticated(self) -> bool:
        """Return True if principal is an authenticated user or merchant."""
        return self.user_id is not None and self.principal_type in ("user", "merchant")

    @property
    def is_guest(self) -> bool:
        """Return True if principal is an anonymous guest."""
        return self.principal_type == "guest"

    @property
    def is_merchant(self) -> bool:
        """Return True if principal is a merchant."""
        return self.principal_type == "merchant" or self.role == "merchant"
