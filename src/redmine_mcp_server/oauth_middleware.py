import os
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import httpx

current_redmine_token: ContextVar[str | None] = ContextVar(
    "current_redmine_token", default=None
)

# Context variable for dynamic API keys (per-request)
current_api_key: ContextVar[str | None] = ContextVar(
    "current_api_key", default=None
)

REDMINE_URL = os.environ.get("REDMINE_URL", "").rstrip("/")
REDMINE_MCP_BASE_URL = os.environ.get(
    "REDMINE_MCP_BASE_URL", "http://localhost:3040"
).rstrip("/")

SKIP_AUTH_PATHS = {
    "/.well-known/oauth-protected-resource",
    "/.well-known/oauth-authorization-server",
    "/health",
    "/revoke",
}

RESOURCE_METADATA_URL = f"{REDMINE_MCP_BASE_URL}/.well-known/oauth-protected-resource"


def _www_authenticate_header(include_error: bool) -> str:
    base = f'Bearer resource_metadata="{RESOURCE_METADATA_URL}"'
    if include_error:
        return base + ', error="invalid_token"'
    return base


class RedmineOAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in SKIP_AUTH_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "error": "unauthorized",
                    "error_description": (
                        "Bearer token required. Server is running in OAuth mode "
                        "(REDMINE_AUTH_MODE=oauth). If you intended legacy mode, "
                        "set REDMINE_AUTH_MODE=legacy and restart the server."
                    ),
                },
                headers={
                    "WWW-Authenticate": _www_authenticate_header(include_error=False)
                },
            )

        token = auth_header.removeprefix("Bearer ").strip()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{REDMINE_URL}/users/current.json",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10,
                )
            except httpx.RequestError:
                return JSONResponse(
                    status_code=503,
                    content={"error": "upstream_unavailable"},
                )

        if response.status_code != 200:
            return JSONResponse(
                status_code=401,
                content={"error": "invalid_token"},
                headers={
                    "WWW-Authenticate": _www_authenticate_header(include_error=True)
                },
            )

        token_var = current_redmine_token.set(token)
        try:
            return await call_next(request)
        finally:
            current_redmine_token.reset(token_var)


def get_current_token() -> str:
    token = current_redmine_token.get()
    if token is None:
        raise RuntimeError("No Redmine token in context — is OAuth middleware active?")
    return token


class DynamicApiKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to extract X-Redmine-API-Key header and set it in context.
    
    This allows each request to use a different Redmine API key,
    enabling multi-user support with different permissions.
    """

    async def dispatch(self, request: Request, call_next):
        # Extract API key from header
        api_key = request.headers.get("X-Redmine-API-Key")

        # Also support query parameter for easier testing
        if not api_key:
            api_key = request.query_params.get("api_key")

        if api_key:
            # Set in context for this request
            api_key_var = current_api_key.set(api_key)
            try:
                return await call_next(request)
            finally:
                current_api_key.reset(api_key_var)
        else:
            # No API key provided, continue without setting context
            return await call_next(request)
