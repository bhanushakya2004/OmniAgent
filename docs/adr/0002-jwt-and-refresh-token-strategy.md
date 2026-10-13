# ADR 0002: JWT Authentication and Refresh Token Rotation Strategy

## Status
Accepted

## Context
OmniMission AI serves both browser-based Next.js applications (for shoppers and store merchants) and programmatic API / mobile clients. Authentication must prevent credential theft and Cross-Site Scripting (XSS) compromise while maintaining high throughput and low database overhead during authenticated API operations.

## Decision
1. **Argon2id Password Hashing:** User passwords are encrypted with Argon2id using parameters: `time_cost=3`, `memory_cost=65536` (64 MB), and `parallelism=4`.
2. **Stateless Access Tokens:** Short-lived (15 minutes) JSON Web Tokens (JWT) signed with HMAC-SHA256 (`HS256`). Claims include subject (`sub`), role (`role`), expiration (`exp`), issued-at (`iat`), and JWT ID (`jti`). Access tokens are validated statelessly by middleware and FastAPI dependencies.
3. **Rotating Refresh Tokens in HttpOnly Cookies:** High-entropy (48 bytes URL-safe) refresh tokens stored in secure, `HttpOnly`, `SameSite=Lax` cookies for web clients, with fallback in the JSON body for native/API clients. Tokens expire in 14 days.
4. **Token Reuse Detection:** Refresh tokens are hashed using SHA-256 before storage in PostgreSQL (`refresh_tokens` table). When a refresh token is presented:
   - If valid and unrevoked, it is immediately revoked and replaced with a new token pair (single-flight rotation).
   - If a previously revoked token is presented (indicating theft or token replay), the system immediately revokes **all** active refresh tokens belonging to that user account, invalidating the entire token family.
5. **RFC 7807 Error Envelope:** All authentication failures return standardized `application/problem+json` error payloads with machine-readable codes (`INVALID_CREDENTIALS`, `TOKEN_REUSE_DETECTED`, `TOKEN_EXPIRED`, `ROLE_NOT_AUTHORIZED`).

## Consequences
- Protects refresh tokens from malicious JavaScript access via HttpOnly cookies.
- Prevents stolen token replays by invalidating all active sessions upon detected reuse.
- Fast, database-free token validation on high-frequency API endpoints.
