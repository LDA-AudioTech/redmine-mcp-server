# Guía de Replicación - Redmine MCP Fork

Cómo replicar este sistema en otra VM desde cero.

## Requisitos Previos

- VM con Docker y Docker Compose
- Dominio o subdominio (ej: nip.io)
- IP pública estática
- Acceso root

## Paso 1: Clonar y Preparar

```bash
# En tu máquina local
git clone https://github.com/jdsanchezlda/redmine-mcp-server.git
cd redmine-mcp-server
git checkout develop
```

## Paso 2: Configurar Docker Compose

```bash
# En la VM
mkdir -p /opt/redmine-mcp
cd /opt/redmine-mcp

# Crear docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  redmine-mcp-server:
    image: ghcr.io/jdsanchezlda/redmine-mcp-server:dynamic-api-key
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

# Crear Caddyfile
cat > Caddyfile << 'EOF'
tu-dominio.nip.io {
    reverse_proxy redmine-mcp-server:8000
}
EOF
```

## Paso 3: Configurar Firewall (GCP)

```bash
# HTTP
gcloud compute firewall-rules create allow-http \
  --direction=INGRESS --priority=900 \
  --network=default --action=ALLOW \
  --rules=tcp:80 --source-ranges=0.0.0.0/0 \
  --target-tags=tu-vm-tag

# HTTPS
gcloud compute firewall-rules create allow-https \
  --direction=INGRESS --priority=900 \
  --network=default --action=ALLOW \
  --rules=tcp:443 --source-ranges=0.0.0.0/0 \
  --target-tags=tu-vm-tag

# Salida para Let's Encrypt
gcloud compute firewall-rules create allow-outbound \
  --direction=EGRESS --priority=1000 \
  --network=default --action=ALLOW \
  --rules=all --destination-ranges=0.0.0.0/0 \
  --target-tags=tu-vm-tag
```

## Paso 4: Deploy

```bash
cd /opt/redmine-mcp
sudo docker-compose up -d

# Verificar
sudo docker logs redmine-mcp-caddy --tail 20
# Debe mostrar: "certificate obtained successfully"
```

## Paso 5: Verificar

```bash
# Health check
curl https://tu-dominio.nip.io/health
# Response: {"status":"ok",...}

# Con API key
curl "https://tu-dominio.nip.io/mcp?api_key=TU_API_KEY"
```

## Troubleshooting

### Caddy no obtiene certificado
- Verificar firewall egress (puerto 443 saliente)
- Verificar que el dominio resuelve a la IP

### 502 Bad Gateway
- Verificar que redmine-mcp-server está running
- Verificar red Docker: `docker network ls`

### API key no funciona
- Verificar logs: `docker logs redmine-mcp-server`
- Probar header: `curl -H "X-Redmine-API-Key: ..."`

## Checklist de Replicación

- [ ] VM creada con Docker
- [ ] Dominio configurado (nip.io o propio)
- [ ] Firewall rules (80, 443, egress)
- [ ] Docker Compose y Caddyfile creados
- [ ] Contenedores corriendo
- [ ] SSL funcionando (Let's Encrypt)
- [ ] Health check responde
- [ ] API key funciona
- [ ] Documentado en README

## Tiempo Estimado

- Setup VM: 10 min
- Firewall: 5 min
- Deploy: 5 min
- SSL (automático): 2 min
- **Total: ~25 min**
