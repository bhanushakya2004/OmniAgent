"""RFC 7807 Problem Details error handling."""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class ProblemDetail(BaseModel):
    """RFC 7807 Problem Details response envelope."""

    type: str = Field(
        default="about:blank", description="URI reference identifying the problem type"
    )
    title: str = Field(description="Short human-readable summary of problem type")
    status: int = Field(description="HTTP status code")
    detail: str = Field(description="Human-readable explanation specific to this occurrence")
    code: str = Field(description="Machine-readable application error code")
    request_id: str | None = Field(default=None, description="Correlated trace request identifier")
    errors: list[dict[str, Any]] | None = Field(
        default=None, description="Field-specific validation errors"
    )


class ProblemException(Exception):
    """Base application exception mapping to RFC 7807 Problem Details."""

    def __init__(
        self,
        status_code: int,
        title: str,
        detail: str,
        code: str,
        errors: list[dict[str, Any]] | None = None,
        type_uri: str = "about:blank",
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.code = code
        self.errors = errors
        self.type_uri = type_uri


class NotFoundError(ProblemException):
    def __init__(self, detail: str, code: str = "NOT_FOUND") -> None:
        super().__init__(status_code=404, title="Resource Not Found", detail=detail, code=code)


class ConflictError(ProblemException):
    def __init__(self, detail: str, code: str = "CONFLICT") -> None:
        super().__init__(status_code=409, title="Conflict", detail=detail, code=code)


class UnauthorizedError(ProblemException):
    def __init__(self, detail: str = "Authentication required", code: str = "UNAUTHORIZED") -> None:
        super().__init__(status_code=401, title="Unauthorized", detail=detail, code=code)


class ForbiddenError(ProblemException):
    def __init__(self, detail: str = "Permission denied", code: str = "FORBIDDEN") -> None:
        super().__init__(status_code=403, title="Forbidden", detail=detail, code=code)


class BadRequestError(ProblemException):
    def __init__(
        self, detail: str, code: str = "BAD_REQUEST", errors: list[dict[str, Any]] | None = None
    ) -> None:
        super().__init__(
            status_code=400, title="Bad Request", detail=detail, code=code, errors=errors
        )


async def problem_exception_handler(request: Request, exc: ProblemException) -> JSONResponse:
    """Handle custom ProblemException instances."""
    request_id = getattr(request.state, "request_id", None)
    content = ProblemDetail(
        type=exc.type_uri,
        title=exc.title,
        status=exc.status_code,
        detail=exc.detail,
        code=exc.code,
        request_id=request_id,
        errors=exc.errors,
    ).model_dump(exclude_none=True)

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        media_type="application/problem+json",
    )
