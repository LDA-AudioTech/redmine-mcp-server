# Redmine MCP Server - LDA AudioTech Fork

Fork corporativo de [jztan/redmine-mcp-server](https://github.com/jztan/redmine-mcp-server) con soporte para **API keys dinámicas por request**.

## Objetivo

Permitir que múltiples usuarios compartan el mismo servidor MCP de Redmine usando sus propias credenciales, sin desplegar una instancia por usuario.

## Endpoint en producción

```text
https://redmine-mcp-34-52-227-235.nip.io/mcp?api_key=TU_API_KEY
```

Health:

```text
https://redmine-mcp-34-52-227-235.nip.io/health
```

## Diferencias con el proyecto original

| Tema | Original | Fork LDA |
|------|----------|----------|
| API key | Global | Dinámica por request |
| Multiusuario | No | Sí |
| Aislamiento por request | No aplica | `ContextVar` |
| HTTPS en producción | Opcional | Sí |

## Cómo se usa

### ChatGPT / clientes que solo aceptan URL

```text
https://redmine-mcp-34-52-227-235.nip.io/mcp?api_key=TU_API_KEY
```

### Clientes que soportan headers

```bash
curl -H "X-Redmine-API-Key: TU_API_KEY" \
  https://redmine-mcp-34-52-227-235.nip.io/mcp
```

## Arquitectura resumida

```text
Cliente MCP
  ↓
Redmine MCP URL + api_key
  ↓
Caddy (TLS / reverse proxy)
  ↓
redmine-mcp-server
  ↓
Redmine
```

### Decisión técnica clave

Prioridad de autenticación:

1. OAuth token
2. API key dinámica
3. cliente legacy

## Despliegue / replicación

Tiempo estimado: **25 minutos**

### Requisitos

- VM con Docker y Docker Compose
- IP pública estática
- dominio o subdominio (por ejemplo `nip.io`)
- acceso root

### Clonar

```bash
git clone https://github.com/LDA-AudioTech/redmine-mcp-server.git
cd redmine-mcp-server
git checkout develop
```

### Configuración mínima de producción

#### `docker-compose.yml`

```yaml
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
```

#### `Caddyfile`

```text
tu-ip.nip.io {
    reverse_proxy redmine-mcp-server:8000
}
```

### Firewall GCP

Abrir:

- `80/tcp`
- `443/tcp`
- salida a internet para Let's Encrypt

### Arranque

```bash
docker-compose up -d
docker logs redmine-mcp-caddy --tail 20
```

### Verificación

```bash
curl https://tu-ip.nip.io/health
curl "https://tu-ip.nip.io/mcp?api_key=TU_API_KEY"
```

## Troubleshooting

### Caddy no obtiene certificado

- revisar salida a internet
- revisar DNS / resolución del dominio

### 502 Bad Gateway

- revisar `docker ps`
- revisar logs de `redmine-mcp-server`
- revisar red Docker

### API key no funciona

- revisar logs del contenedor
- probar con header `X-Redmine-API-Key`

## Documentación técnica

### SDD archivado

Los artefactos formales del cambio viven en:

- `openspec/changes/archive/2026-04-15-redmine-mcp-dynamic-api-keys/`

Contiene:

- `proposal.md`
- `spec.md`
- `design.md`
- `tasks.md`

### Documentación original del upstream

- [README original](https://github.com/jztan/redmine-mcp-server/blob/master/README.md)
- [Tool Reference](https://github.com/jztan/redmine-mcp-server/blob/master/docs/tool-reference.md)

## Repositorio e imagen

- **Repo**: `https://github.com/LDA-AudioTech/redmine-mcp-server`
- **Imagen**: `ghcr.io/lda-audiotech/redmine-mcp-server:dynamic-api-key`

## Licencia

MIT - ver [LICENSE](LICENSE)
