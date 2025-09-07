# 🚀 Signal Bloom Deployment Guide

This guide covers various deployment options for Signal Bloom, from development to production.

## Quick Start (Development)

### Local Development
```bash
# Backend
cd backend
pip install -r requirements.txt
python main.py

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Access at: http://localhost:5173

## Production Deployment Options

### 1. Docker Deployment (Recommended)

#### Prerequisites
- Docker
- Docker Compose
- ElevenLabs API key (optional, for voice features)

#### Setup
```bash
# Clone repository
git clone <repository-url>
cd 6degrees-signalbloom

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your settings

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs
```

#### Production with Nginx
```bash
# Start with production profile (includes Nginx)
docker-compose --profile production up -d

# Services will be available at:
# - Application: http://localhost (port 80)
# - Backend API: http://localhost/api/
# - WebSocket: ws://localhost/ws
```

### 2. Manual Deployment

#### Backend Production Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt gunicorn

# Set production environment
export DEBUG=false
export LOG_LEVEL=info
export DATABASE_URL=sqlite:///data/signals.db
export CORS_ORIGINS='["https://yourdomain.com"]'

# Create data directory
mkdir -p data

# Start with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Frontend Production Build
```bash
cd frontend

# Install dependencies
npm ci

# Build for production
npm run build

# Serve with static server
npm install -g serve
serve -s build -l 3000
```

### 3. Cloud Deployment

#### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

#### Heroku
```bash
# Create Procfile for backend
echo "web: gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:\$PORT" > backend/Procfile

# Deploy
heroku create your-app-name
git push heroku main
```

#### Vercel (Frontend only)
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy frontend
cd frontend
vercel --prod
```

## Environment Configuration

### Core Settings
```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=info

# Database
DATABASE_URL=sqlite:///data/signals.db

# Security
SECRET_KEY=your-super-secret-key-here
CORS_ORIGINS=["https://yourdomain.com"]

# Performance
MAX_SIGNALS=1000
SIGNAL_CLEANUP_INTERVAL=3600
```

### Voice Integration
```bash
# ElevenLabs API
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_VOICE_ID=your_voice_id_here
ELEVENLABS_BASE_URL=https://api.elevenlabs.io
```

### Security Settings
```bash
# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# CORS (adjust for your domain)
CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]
```

## SSL/HTTPS Setup

### With Nginx (Recommended)
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # Include the existing nginx.conf configuration
    include /etc/nginx/conf.d/signal-bloom.conf;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### With Let's Encrypt
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Database Setup

### SQLite (Default)
- Automatic setup, no configuration needed
- Suitable for small to medium deployments
- File-based storage in `data/signals.db`

### PostgreSQL (Production)
```bash
# Environment configuration
DATABASE_URL=postgresql://user:password@localhost/signalbloom

# Install dependencies
pip install psycopg2-binary
```

### Database Migration
```python
# Create migration script
from database import db_manager
import asyncio

async def migrate():
    await db_manager.initialize()
    print("Database migrated successfully")

asyncio.run(migrate())
```

## Monitoring & Maintenance

### Health Checks
```bash
# Backend health
curl http://localhost:8000/status

# Voice service health
curl http://localhost:8000/voice/status

# Docker health
docker-compose ps
```

### Logs
```bash
# Docker logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Production logs
tail -f /var/log/signal-bloom/backend.log
tail -f /var/log/signal-bloom/nginx.log
```

### Database Maintenance
```bash
# Backup database
cp backend/data/signals.db backup/signals_$(date +%Y%m%d).db

# Check database size
du -h backend/data/signals.db

# Manual cleanup (if needed)
python3 -c "
from database import db_manager
import asyncio
asyncio.run(db_manager.cleanup_old_signals(500))
"
```

## Performance Optimization

### Backend Optimization
```bash
# Use more workers for high traffic
gunicorn main:app -w 8 -k uvicorn.workers.UvicornWorker

# Enable connection pooling for PostgreSQL
DATABASE_URL=postgresql://user:pass@host/db?pool_size=20&max_overflow=0
```

### Frontend Optimization
```bash
# Build with optimizations
npm run build

# Use CDN for static assets
# Configure in vite.config.js:
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        vendor: ['svelte']
      }
    }
  }
}
```

### Nginx Optimization
```nginx
# Enable gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript;

# Enable caching
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Troubleshooting

### Common Issues

#### WebSocket Connection Failed
```bash
# Check backend is running
curl http://localhost:8000/status

# Check firewall
sudo ufw allow 8000

# Check CORS settings
echo $CORS_ORIGINS
```

#### Voice Features Not Working
```bash
# Check API key
echo $ELEVENLABS_API_KEY

# Test API connectivity
curl -H "xi-api-key: $ELEVENLABS_API_KEY" https://api.elevenlabs.io/v1/voices

# Check browser console for Web Speech API errors
```

#### Database Issues
```bash
# Check database file permissions
ls -la backend/data/

# Recreate database
rm backend/data/signals.db
python3 -c "from database import db_manager; import asyncio; asyncio.run(db_manager.initialize())"
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
export LOG_LEVEL=debug

# Run with verbose output
python main.py
```

## Scaling

### Horizontal Scaling
```yaml
# docker-compose.yml for multiple backend instances
version: '3.8'
services:
  backend1:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://user:pass@db/signalbloom
  
  backend2:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://user:pass@db/signalbloom
  
  nginx:
    image: nginx
    depends_on:
      - backend1
      - backend2
```

### Load Balancing
```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    keepalive 32;
}
```

## Security Checklist

- [ ] Change default secret key
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Use strong passwords
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Backup database regularly

## Support

- Check logs for error details
- Test with `./test.sh` script
- Verify environment configuration
- Review this deployment guide
- Check GitHub issues

---

**Need help?** Open an issue on GitHub with:
- Deployment method used
- Error messages
- Environment configuration (without secrets)
- Steps to reproduce