"""Global error handler — consistent JSON error shape per SRS §9."""
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "Validation error"},
    )


async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "message": str(exc)},
    )


async def permission_error_handler(request: Request, exc: PermissionError):
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc), "message": str(exc)},
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred", "message": "Something went wrong. Please try again."},
    )
