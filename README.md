# Redmine MCP Server - Dynamic API Key Fork

Fork de [jztan/redmine-mcp-server](https://github.com/jztan/redmine-mcp-server) con soporte para **API keys dinámicas por request**.

Permite múltiples usuarios concurrentes con sus propias credenciales de Redmine, ideal para despliegues multi-usuario.

## 🚀 Producción Actual

**URL**: `https://redmine-mcp-34-52-227-235.nip.io/mcp?api_key=TU_API_KEY`

**Estado**: ✅ Funcionando con SSL (Let's Encrypt)

---

## Diferencias con el Original

| Feature | Original | Este Fork |
|---------|----------|-----------|
| API Key | Global (una para todos) | Dinámica (por request) |
| Multi-usuario | ❌ No soportado | ✅ Soportado |
| Thread-safe | ❌ No aplica | ✅ ContextVars |
| HTTPS | Opcional | ✅ Obligatorio (Let's Encrypt) |

---

## Uso

### ChatGPT / Claude (URL simple)

```
https://redmine-mcp-34-52-227-235.nip.io/mcp?api_key=TU_API_KEY
```

### Headers (alternativa)

```bash
curl -H "X-Redmine-API-Key: TU_API_KEY" \
  https://redmine-mcp-34-52-227-235.nip.io/mcp
```

---

## Arquitectura

### Componentes

1. **DynamicApiKeyMiddleware**: Extrae API key de header `X-Redmine-API-Key` o query param `api_key`
2. **current_api_key ContextVar**: Almacenamiento thread-safe por request
3. **_get_redmine_client()**: Prioridad OAuth token > API key dinámica > Legacy client

### Data Flow

```
Request → Middleware → ContextVar → _get_redmine_client() → Redmine API
```

### Infraestructura

- **Docker**: Contenedores MCP + Caddy
- **SSL**: Let's Encrypt automático
- **Proxy**: Caddy (reverse proxy + SSL termination)

---

## Cómo Replicar Este Sistema

Tiempo estimado: **25 minutos**

### Requisitos Previos

- VM con Docker y Docker Compose instalado
- IP pública estática
- Dominio o subdominio (ej: `tu-ip.nip.io`)
- Acceso root a la VM

### Paso 1: Clonar el Fork

```bash
# En tu máquina local o directamente en la VM
git clone https://github.com/LDA-AudioTech/redmine-mcp-server.git
cd redmine-mcp-server
git checkout develop
```

### Paso 2: Configurar Docker Compose

```bash
# En la VM
mkdir -p /opt/redmine-mcp
cd /opt/redmine-mcp

# Crear docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  redmine-mcp-server:
    image: ghcr.io/lda-audiotech/redmine-mcp-server:dynamic-api-key
    container_name: redmine-mcp-server
    restart: unless-stopped
    environment:
      REDMINE_URL: https://tu-redmine.com
      REDMINE_AUTH_MODE: legacy
    networks:
      - mcp-network

  caddy:
    image: caddy:2-alpine
    container_name: redmine-mcp-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
    networks:
      - mcp-network

volumes:
  caddy-data:

networks:
  mcp-network:
    driver: bridge
EOF

# Crear Caddyfile (reemplaza TU_IP con tu IP pública)
cat > Caddyfile << 'EOF'
tu-ip.nip.io {
    reverse_proxy redmine-mcp-server:8000
}
EOF
```

### Paso 3: Configurar Firewall (GCP)

```bash
# Permitir HTTP
gcloud compute firewall-rules create allow-http \
  --direction=INGRESS --priority=900 \
  --network=default --action=ALLOW \
  --rules=tcp:80 --source-ranges=0.0.0.0/0 \
  --target-tags=tu-vm-tag

# Permitir HTTPS
gcloud compute firewall-rules create allow-https \
  --direction=INGRESS --priority=900 \
  --network=default --action=ALLOW \
  --rules=tcp:443 --source-ranges=0.0.0.0/0 \
  --target-tags=tu-vm-tag

# Permitir salida (para Let's Encrypt)
gcloud compute firewall-rules create allow-outbound \
  --direction=EGRESS --priority=1000 \
  --network=default --action=ALLOW \
  --rules=all --destination-ranges=0.0.0.0/0 \
  --target-tags=tu-vm-tag
```

### Paso 4: Deploy

```bash
cd /opt/redmine-mcp
sudo docker-compose up -d

# Verificar que Caddy obtuvo el certificado SSL
sudo docker logs redmine-mcp-caddy --tail 20
# Debe mostrar: "certificate obtained successfully"
```

### Paso 5: Verificar Funcionamiento

```bash
# Health check
curl https://tu-ip.nip.io/health
# Response: {"status":"ok","service":"redmine_mcp_tools",...}

# Test con API key
curl "https://tu-ip.nip.io/mcp?api_key=TU_API_KEY"
```

### Troubleshooting

**Caddy no obtiene certificado:**
- Verificar firewall egress (puerto 443 saliente)
- Verificar que el dominio resuelve a la IP: `dig +short tu-ip.nip.io`

**Error 502 Bad Gateway:**
- Verificar que redmine-mcp-server está running: `docker ps`
- Verificar red Docker: `docker network inspect redmine-mcp_mcp-network`

**API key no funciona:**
- Verificar logs: `docker logs redmine-mcp-server --tail 50`
- Probar con header: `curl -H "X-Redmine-API-Key: ..." https://...`

---

## Archivos Modificados

### 1. `src/redmine_mcp_server/oauth_middleware.py`

```python
# Context variable para API keys dinámicas
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

### 2. `src/redmine_mcp_server/redmine_handler.py`

```python
def _get_redmine_client() -> Redmine:
    global _legacy_client

    if redmine is not None:
        return redmine

    from .oauth_middleware import current_redmine_token, current_api_key

    # Priority 1: OAuth token (Bearer)
    token = current_redmine_token.get()
    if token:
        return Redmine(REDMINE_URL, requests={"headers": {"Authorization": f"Bearer {token}"}})

    # Priority 2: Dynamic API key
    api_key = current_api_key.get()
    if api_key:
        return Redmine(REDMINE_URL, key=api_key)

    # Priority 3: Legacy mode (cached singleton)
    if _legacy_client is None:
        _legacy_client = _build_legacy_client()
    return _legacy_client
```

### 3. `src/redmine_mcp_server/main.py`

```python
from .oauth_middleware import DynamicApiKeyMiddleware
app.add_middleware(DynamicApiKeyMiddleware)
```

---

## SDD (Software Design Document)

Los artefactos SDD completos están en:
- **Engram**: `sdd/redmine-mcp-dynamic-api-keys/{proposal,spec,design,tasks,archive-report}`
- **Filesystem**: `openspec/changes/archive/2026-04-15-redmine-mcp-dynamic-api-keys/`

### Resumen

**Intent**: Soporte multi-usuario con API keys dinámicas
**Scope**: Middleware, contextvars, integración con cliente Redmine
**Risk**: Bajo (cambios aditivos, backward compatible)

### Requisitos

**Funcionales:**
- FR1: Extraer API key de header `X-Redmine-API-Key`
- FR2: Extraer API key de query param `api_key`
- FR3: Almacenar en ContextVar (thread-safe)
- FR4: Usar en cliente Redmine con fallback a legacy

**No funcionales:**
- NFR1: Thread-safe (contextvars)
- NFR2: HTTPS obligatorio en producción
- NFR3: Backward compatible

### Tareas Completadas

- [x] Agregar `current_api_key` ContextVar
- [x] Crear `DynamicApiKeyMiddleware`
- [x] Modificar `_get_redmine_client()`
- [x] Registrar middleware en `main.py`
- [x] Corregir versión PEP 440
- [x] CI/CD GitHub Actions
- [x] Build y push Docker image
- [x] Deploy en VM GCP
- [x] Configurar Caddy + Let's Encrypt SSL
- [x] Firewall rules (80, 443)
- [x] Tests pasando

---

## Repositorio e Imagen

- **Fork**: https://github.com/LDA-AudioTech/redmine-mcp-server
- **Imagen Docker**: `ghcr.io/lda-audiotech/redmine-mcp-server:dynamic-api-key`
- **Package**: `ghcr.io/lda-audiotech/redmine-mcp-server`

---

## Documentación Original

Para documentación completa de las herramientas MCP disponibles, ver:
- [README original](https://github.com/jztan/redmine-mcp-server/blob/master/README.md)
- [Tool Reference](https://github.com/jztan/redmine-mcp-server/blob/master/docs/tool-reference.md)

---

## Licencia

MIT - Ver [LICENSE](LICENSE)
