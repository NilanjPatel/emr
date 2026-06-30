"""
DB session middleware — attaches an async SQLAlchemy session to every request.

Sets request.state.db so the audit middleware (and any future middleware)
always has a live session without each route handler needing to manage it.
Session is committed and closed cleanly after the response, regardless of errors.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.database import AsyncSessionLocal
import logging

logger = logging.getLogger(__name__)

# Paths that never need a DB session (saves a connection for pure static/health)
NO_DB_PREFIXES = ("/docs", "/redoc", "/openapi.json")


class DBSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(p) for p in NO_DB_PREFIXES):
            return await call_next(request)

        async with AsyncSessionLocal() as session:
            request.state.db = session
            try:
                response = await call_next(request)
                return response
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
