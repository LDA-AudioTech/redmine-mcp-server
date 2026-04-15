# Resumen - Redmine MCP Fork con API Keys Dinámicas

## Estado Final
✅ **IMPLEMENTADO Y DESPLEGADO**

## Logros

### 1. Código Modificado ✅
- **Middleware** (`oauth_middleware.py`): Agregado `DynamicApiKeyMiddleware` que extrae API keys de headers o query params
- **Handler** (`redmine_handler.py`): Actualizado para usar API keys dinámicas cuando están disponibles
- **Main** (`main.py`): Registrado middleware en la app FastAPI
- **Versión**: Corregida de `1.3.0-lda` a `1.3.0+lda` (PEP 440 compliant)

### 2. CI/CD Configurado ✅
- GitHub Actions workflow creado (`.github/workflows/docker-build.yml`)
- Imagen automáticamente buildeada y pusheada a GitHub Container Registry

### 3. Deploy Completado ✅
- **Imagen**: `ghcr.io/jdsanchezlda/redmine-mcp-server:dynamic-api-key`
- **VM**: 34.52.227.235 (europe-west1-b)
- **Ubicación**: `/opt/redmine-mcp/`
- **Estado**: Contenedor corriendo

## Configuración Actual

### Docker Compose
```yaml
services:
  redmine-mcp-server:
    image: ghcr.io/jdsanchezlda/redmine-mcp-server:dynamic-api-key
    environment:
      - REDMINE_URL=https://dev.pm.lda-audiotech.com
      # REDMINE_API_KEY removed - ahora se pasa por request
```

### Uso

**Header:**
```bash
curl -H "X-Redmine-API-Key: TU_API_KEY" \
  http://redmine-mcp-34-52-227-235.nip.io/tools
```

**Query param:**
```bash
curl "http://redmine-mcp-34-52-227-235.nip.io/tools?api_key=TU_API_KEY"
```

## Issues Pendientes

1. **Firewall HTTP/HTTPS**: Las reglas están creadas pero parece haber problemas de acceso desde fuera
2. **Healthcheck**: El contenedor está marcado como "unhealthy" porque el healthcheck necesita una API key válida

## Repositorio
- **Fork**: https://github.com/jdsanchezlda/redmine-mcp-server
- **Branch**: develop
- **Package**: https://github.com/jdsanchezlda/redmine-mcp-server/pkgs/container/redmine-mcp-server

## Comandos Útiles

```bash
# Ver logs
sudo docker logs redmine-mcp-server --tail 50

# Reiniciar
cd /opt/redmine-mcp && sudo docker-compose restart

# Ver estado
sudo docker ps
```
