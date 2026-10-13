"""Unified Principal domain model representing authenticated users or anonymous guests."""

import uuid
from dataclasses import dataclass
from typing import Literal

from omnimission.models.user import User


@dataclass
class Principal:
    """Represents the calling identity (authenticated user, merchant, or anonymous guest)."""

    principal_type: Literal["guest", "user", "merchant"]
    user_id: uuid.UUID | None
    guest_session_id: uuid.UUID | None
    session_token: str | None
    email: str | None = None
    role: str | None = None
    user: User | None = None

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
        return self.principal_type == "merchant"
