# Redmine MCP Server - Dynamic API Key Fork

Fork de [jztan/redmine-mcp-server](https://github.com/jztan/redmine-mcp-server) con soporte para **API keys dinámicas por request**.

Permite múltiples usuarios concurrentes con sus propias credenciales de Redmine, ideal para despliegues multi-usuario.

## 🚀 Producción

**URL**: `https://redmine-mcp-34-52-227-235.nip.io/mcp?api_key=TU_API_KEY`

## Diferencias con el Original

| Feature | Original | Este Fork |
|---------|----------|-----------|
| API Key | Global (una para todos) | Dinámica (por request) |
| Multi-usuario | ❌ No soportado | ✅ Soportado |
| Thread-safe | ❌ No aplica | ✅ ContextVars |
| HTTPS | Opcional | ✅ Obligatorio (Let's Encrypt) |

## Uso

### ChatGPT / Claude

```
https://redmine-mcp-34-52-227-235.nip.io/mcp?api_key=65487679e7363a0d06605c9fec28430f2fc43884
```

### Headers (alternativa)

```bash
curl -H "X-Redmine-API-Key: TU_API_KEY" \
  https://redmine-mcp-34-52-227-235.nip.io/mcp
```

## Implementación

- **Middleware**: `DynamicApiKeyMiddleware` extrae API key de header/query param
- **Storage**: `contextvars` para thread-safety por request
- **Prioridad**: OAuth token > API key dinámica > Legacy client
- **SSL**: Let's Encrypt automático via Caddy

## Repositorio

- **Fork**: https://github.com/jdsanchezlda/redmine-mcp-server
- **Imagen**: `ghcr.io/jdsanchezlda/redmine-mcp-server:dynamic-api-key`

## Documentación Original

Para documentación completa de herramientas MCP, ver [README original](https://github.com/jztan/redmine-mcp-server/blob/master/README.md).

## Licencia

MIT - Ver [LICENSE](LICENSE)
