# Docker Setup Guide

This guide explains how to run the Signup Bot using Docker and Docker Compose.

## Prerequisites

- Docker and Docker Compose installed
- Discord Bot Token
- Firebase credentials (JSON file)
- Clash of Clans API token

## Quick Start

### 1. Prepare Environment Variables

Copy the example environment file:
```bash
cp env.example .env
```

### 2. Encode Firebase Credentials

Use the provided script to encode your Firebase JSON file:
```bash
python encode_firebase.py path/to/your/firebase-credentials.json
```

Copy the output and update your `.env` file:
```bash
# Edit .env file
FIREBASE_CRED=your_base64_encoded_credentials_here
```

### 3. Update Environment Variables

Edit the `.env` file with your credentials:
```bash
# Required variables
DISCORD_TOKEN=your_discord_bot_token
FIREBASE_CRED=your_base64_encoded_firebase_credentials
AUTH=your_clash_of_clans_api_token

# Optional variables
ENVIRONMENT=prod
API_BASE_URL=http://localhost:8001
```

### 4. Build and Run

```bash
# Build the images
docker-compose build

# Start the services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Docker Configuration Details

### Services

#### Bot Service
- **Container**: `signup-bot`
- **Purpose**: Discord bot application
- **Dependencies**: API service
- **Health Check**: Monitors API connectivity

#### API Service
- **Container**: `signup-api`
- **Purpose**: REST API server
- **Port**: 8080 (exposed to host)
- **Health Check**: Monitors API endpoint

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_TOKEN` | ✅ | Discord bot token |
| `FIREBASE_CRED` | ✅ | Base64 encoded Firebase credentials |
| `AUTH` | ✅ | Clash of Clans API token |
| `ENVIRONMENT` | ❌ | Environment (dev/prod, defaults to dev) |
| `API_BASE_URL` | ❌ | API base URL (auto-configured in Docker) |

### Volumes

- `./data:/app/data`: Persistent data storage
- Environment variables loaded from `.env` file

### Networks

- `signup-network`: Internal network for bot-API communication

## Production Deployment

### 1. Environment Setup
```bash
# Set production environment
ENVIRONMENT=prod

# Use production Firebase credentials
FIREBASE_CRED=your_production_base64_credentials
```

### 2. Security Considerations
- ✅ Non-root user in containers
- ✅ Environment variables for secrets
- ✅ No sensitive files in images
- ✅ Health checks for monitoring

### 3. Scaling
```bash
# Scale API service (if needed)
docker-compose up -d --scale api=2

# Scale bot service (if needed)
docker-compose up -d --scale bot=2
```

## Troubleshooting

### Common Issues

#### 1. Environment Variables Not Loading
```bash
# Check if .env file exists
ls -la .env

# Verify environment variables
docker-compose exec bot env | grep FIREBASE_CRED
```

#### 2. Firebase Connection Issues
```bash
# Check Firebase credentials
docker-compose exec api python -c "
from signup_bot import Config
print('Firebase credentials loaded:', bool(Config.FIREBASE_CRED))
"
```

#### 3. API Connection Issues
```bash
# Check API health
curl http://localhost:8080/health

# Check container logs
docker-compose logs api
```

#### 4. Bot Connection Issues
```bash
# Check bot logs
docker-compose logs bot

# Verify Discord token
docker-compose exec bot python -c "
import os
print('Discord token set:', bool(os.getenv('DISCORD_TOKEN')))
"
```

### Health Checks

The containers include health checks:
- **API**: Checks if API responds on port 8080
- **Bot**: Checks if it can connect to API service

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f bot
docker-compose logs -f api

# View recent logs
docker-compose logs --tail=100
```

## Development vs Production

### Development
```bash
# Use development environment
ENVIRONMENT=dev

# Run with logs visible
docker-compose up
```

### Production
```bash
# Use production environment
ENVIRONMENT=prod

# Run in background
docker-compose up -d

# Monitor with logs
docker-compose logs -f
```

## Security Best Practices

1. **Never commit `.env` files** - They contain sensitive data
2. **Use encoded Firebase credentials** - No JSON files in containers
3. **Non-root containers** - Security through isolation
4. **Health checks** - Monitor service health
5. **Restart policies** - Automatic recovery from failures

## Performance Optimization

### Resource Limits
```yaml
# Add to docker-compose.yml services
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M
      cpus: '0.25'
```

### Caching
- Requirements are cached in Docker layers
- Application code is copied after dependencies
- Data directory is mounted for persistence

## Monitoring

### Health Status
```bash
# Check container health
docker-compose ps

# Check health check status
docker inspect signup-bot | grep -A 10 Health
```

### Metrics
```bash
# Container resource usage
docker stats

# Log analysis
docker-compose logs | grep ERROR
``` 