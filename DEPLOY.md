# Deploy Instructions - Redmine MCP Server with Dynamic API Keys

## Status
✅ Docker image built and pushed to GitHub Container Registry
❌ VM still unreachable (34.52.227.235)

## What Was Done
1. Forked repository from jztan/redmine-mcp-server
2. Added dynamic API key support:
   - Middleware extracts API key from header `X-Redmine-API-Key` or query param `api_key`
   - Contextvars store API key per request (thread-safe)
   - Redmine client uses dynamic key when available
3. Fixed PEP 440 version format (1.3.0-lda → 1.3.0+lda)
4. Created GitHub Actions workflow for Docker builds
5. Updated Dockerfile to use pip instead of uv

## Docker Image
- **Registry**: GitHub Container Registry (ghcr.io)
- **Image**: `ghcr.io/jdsanchezlda/redmine-mcp-server`
- **Tags**: `develop`, `dynamic-api-key`, `latest`
- **URL**: https://github.com/jdsanchezlda/redmine-mcp-server/pkgs/container/redmine-mcp-server

## Next Steps (When VM is Available)

### 1. Update docker-compose.yml

```yaml
services:
  redmine-mcp:
    image: ghcr.io/jdsanchezlda/redmine-mcp-server:dynamic-api-key
    container_name: redmine-mcp-server
    ports:
      - "8000:8000"
    environment:
      # Remove REDMINE_API_KEY - no longer needed globally
      - REDMINE_URL=https://redmine.lda-audiotech.com
      # Add any other config vars needed (except API key)
    restart: unless-stopped
```

### 2. Deploy Commands

```bash
# SSH to VM (when available)
gcloud compute ssh redmine-mcp-server --zone=europe-west1-b

# Pull new image
docker pull ghcr.io/jdsanchezlda/redmine-mcp-server:dynamic-api-key

# Stop and remove old container
docker-compose down

# Update docker-compose.yml (copy from above)
nano /opt/docker-compose.yml

# Start with new image
docker-compose up -d

# Verify it's running
docker logs redmine-mcp-server
```

### 3. Test Dynamic API Keys

```bash
# Test with header
curl -H "X-Redmine-API-Key: TU_API_KEY" \
  https://redmine-mcp-34-52-227-235.nip.io/tools

# Test with query param
curl "https://redmine-mcp-34-52-227-235.nip.io/tools?api_key=TU_API_KEY"
```

## Key Changes Summary

| File | Change |
|------|--------|
| `oauth_middleware.py` | Added `current_api_key` contextvar and `DynamicApiKeyMiddleware` |
| `redmine_handler.py` | Updated `_get_redmine_client()` to use dynamic key |
| `main.py` | Registered middleware in FastAPI app |
| `pyproject.toml` | Fixed version format |
| `Dockerfile` | Use pip instead of uv |
| `.github/workflows/docker-build.yml` | CI/CD for Docker builds |

## Troubleshooting

### VM Not Responding
- Check GCP console for VM status
- Verify firewall rules allow SSH (port 22) via IAP
- May need to recreate VM if OS is corrupted

### Image Pull Issues
```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u jdsanchezlda --password-stdin
```

### Permission Issues
Ensure VM has internet access to pull from ghcr.io
