# SDD - Redmine MCP Fork: Dynamic API Keys

## Change Information
- **Change ID**: redmine-mcp-dynamic-api-keys
- **Status**: ✅ COMPLETED
- **Date**: 2026-04-15
- **Author**: jdsanchez

## Intent
Implementar soporte para API keys dinámicas por request en el redmine-mcp-server, permitiendo múltiples usuarios concurrentes con sus propias credenciales de Redmine.

## Requirements

### Functional Requirements
1. Extraer API key de header `X-Redmine-API-Key`
2. Extraer API key de query parameter `api_key`
3. Usar API key dinámica para autenticar con Redmine
4. Mantener compatibilidad con modo legacy (sin cambios)

### Non-Functional Requirements
1. Thread-safe (usar contextvars)
2. HTTPS obligatorio para producción
3. CI/CD automatizado
4. Tests pasando

## Architecture

### Component Changes
```
src/redmine_mcp_server/
├── oauth_middleware.py    # +DynamicApiKeyMiddleware
├── redmine_handler.py     # Modified _get_redmine_client()
└── main.py               # +Middleware registration
```

### Data Flow
1. Request llega con API key en header o query param
2. DynamicApiKeyMiddleware extrae y guarda en contextvar
3. _get_redmine_client() usa API key del contexto
4. Cliente Redmine se crea con API key dinámica

## Implementation

### Code Changes

#### 1. oauth_middleware.py
```python
# Context variable for dynamic API keys
current_api_key: ContextVar[str | None] = ContextVar(
    "current_api_key", default=None
)

class DynamicApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get("X-Redmine-API-Key")
        if not api_key:
            api_key = request.query_params.get("api_key")
        
        if api_key:
            api_key_var = current_api_key.set(api_key)
            try:
                return await call_next(request)
            finally:
                current_api_key.reset(api_key_var)
        else:
            return await call_next(request)
```

#### 2. redmine_handler.py
```python
def _get_redmine_client() -> Redmine:
    # Priority 1: OAuth token
    token = current_redmine_token.get()
    if token:
        return Redmine(REDMINE_URL, requests={"headers": {"Authorization": f"Bearer {token}"}})
    
    # Priority 2: Dynamic API key
    api_key = current_api_key.get()
    if api_key:
        return Redmine(REDMINE_URL, key=api_key)
    
    # Priority 3: Legacy client
    if _legacy_client is None:
        _legacy_client = _build_legacy_client()
    return _legacy_client
```

#### 3. main.py
```python
from .oauth_middleware import DynamicApiKeyMiddleware
app.add_middleware(DynamicApiKeyMiddleware)
```

## Infrastructure

### Docker Compose
- Image: `ghcr.io/jdsanchezlda/redmine-mcp-server:dynamic-api-key`
- Proxy: Caddy (Let's Encrypt SSL)
- Ports: 80, 443

### SSL/TLS
- Provider: Let's Encrypt (automated)
- Domain: redmine-mcp-34-52-227-235.nip.io
- Auto-renewal: Yes

### Firewall Rules
- allow-home-http: 80/tcp
- allow-home-https: 443/tcp
- allow-docker-outbound: Egress all

## Testing

### Test Results
- ✅ All CI tests passing
- ✅ API key extraction working
- ✅ HTTPS endpoint working
- ✅ Health check responding

### Verified URLs
```
HTTPS: https://redmine-mcp-34-52-227-235.nip.io/health
MCP: https://redmine-mcp-34-52-227-235.nip.io/mcp
```

## Deployment

### VM Details
- IP: 34.52.227.235
- Zone: europe-west1-b
- Path: /opt/redmine-mcp/

### Production URL
```
https://redmine-mcp-34-52-227-235.nip.io/mcp?api_key=65487679e7363a0d06605c9fec28430f2fc43884
```

## References
- Repository: https://github.com/jdsanchezlda/redmine-mcp-server
- Package: ghcr.io/jdsanchezlda/redmine-mcp-server:dynamic-api-key
