# Garden Docker Setup

Complete containerized deployment for the Garden platform with backend API, MLflow tracking, and React frontend.

## 🐳 Architecture

```
┌─────────────────────────────────────────────────┐
│               Docker Network                     │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────┐│
│  │   Frontend   │  │   Backend    │  │ MLflow ││
│  │  (React +    │  │   (FastAPI)  │  │   UI   ││
│  │   Nginx)     │  │              │  │        ││
│  │              │  │  Garden API  │  │        ││
│  │  Port: 3000  │  │  Port: 8000  │  │ :5000  ││
│  └──────┬───────┘  └──────┬───────┘  └───┬────┘│
│         │                 │              │     │
│         └─────────────────┴──────────────┘     │
│                                                  │
└─────────────────────────────────────────────────┘
           │              │              │
           ▼              ▼              ▼
      Browser API   mlruns/    garden_data/
                   (volumes)    (volumes)
```

## 🚀 Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+

### Launch Everything

```bash
# Build and start all services
docker-compose -f docker-compose.garden.yml up --build

# Or run in detached mode
docker-compose -f docker-compose.garden.yml up -d --build
```

**Access Points:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MLflow UI**: http://localhost:5000

### Stop Services

```bash
# Stop all containers
docker-compose -f docker-compose.garden.yml down

# Stop and remove volumes (WARNING: deletes data)
docker-compose -f docker-compose.garden.yml down -v
```

## 📦 Services

### 1. Backend (FastAPI)

**Image**: Custom (Python 3.10 slim)  
**Port**: 8000  
**Volumes**:
- `./mlruns` → `/app/mlruns` (MLflow data)
- `./garden_data` → `/app/garden_data` (Garden state)

**Endpoints**:
- `GET /` - Health check
- `GET /docs` - Swagger UI
- `GET /models` - List models
- `POST /models` - Create model
- `POST /models/{id}/compatible` - Find compatible models
- `GET /models/elo/leaderboard` - ELO rankings
- `POST /matches` - Run match
- See full API at http://localhost:8000/docs

### 2. MLflow UI

**Image**: python:3.10-slim  
**Port**: 5000  
**Volumes**:
- `./mlruns` → `/mlruns` (tracking data)

**Features**:
- View all experiments
- Compare runs
- Download artifacts
- Search and filter

### 3. Frontend (React + Nginx)

**Image**: Multi-stage (Node 18 builder + Nginx alpine)  
**Port**: 3000 (mapped to 80 in container)  

**Features**:
- Drag-and-drop arena builder
- ELO-based model suggestions
- Real-time experiment dashboard
- API proxy through Nginx

## 🛠️ Development

### Rebuild Specific Service

```bash
# Rebuild backend only
docker-compose -f docker-compose.garden.yml build backend

# Rebuild and restart backend
docker-compose -f docker-compose.garden.yml up -d --build backend
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.garden.yml logs -f

# Specific service
docker-compose -f docker-compose.garden.yml logs -f backend
docker-compose -f docker-compose.garden.yml logs -f frontend
docker-compose -f docker-compose.garden.yml logs -f mlflow
```

### Execute Commands in Containers

```bash
# Shell in backend
docker-compose -f docker-compose.garden.yml exec backend /bin/bash

# Python shell in backend
docker-compose -f docker-compose.garden.yml exec backend python

# Test API endpoint
docker-compose -f docker-compose.garden.yml exec backend curl http://localhost:8000/
```

### Local Development with Hot Reload

For active development, you may want to run services locally:

```bash
# Run only MLflow in Docker
docker-compose -f docker-compose.garden.yml up mlflow

# Run backend locally with hot reload
cd /Users/jg/mind
uvicorn api.main:app --reload --port 8000

# Run frontend locally with hot reload
cd frontend
npm run dev
```

## 📁 Persistent Data

Data is stored in Docker volumes and local directories:

```
/Users/jg/mind/
├── mlruns/              # MLflow experiments & runs
│   ├── 0/               # Default experiment
│   ├── 1/               # Arena experiments
│   └── ...
├── garden_data/         # Garden state snapshots
│   └── garden_state_*.json
```

**Backup Data:**
```bash
# Create backup
tar -czf garden-backup-$(date +%Y%m%d).tar.gz mlruns/ garden_data/

# Restore backup
tar -xzf garden-backup-YYYYMMDD.tar.gz
```

## 🔧 Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Backend
PYTHONUNBUFFERED=1
ELO_K_FACTOR=32
INITIAL_RATING=1500

# MLflow
MLFLOW_TRACKING_URI=./mlruns

# Frontend (build-time)
VITE_API_BASE_URL=http://localhost:8000
```

### Custom Ports

Edit `docker-compose.garden.yml`:

```yaml
services:
  backend:
    ports:
      - "8080:8000"  # Change 8080 to your preferred port
  
  frontend:
    ports:
      - "3001:80"    # Change 3001 to your preferred port
```

## 🧪 Testing

### Health Checks

```bash
# Backend health
curl http://localhost:8000/

# MLflow UI
curl http://localhost:5000/

# Frontend
curl http://localhost:3000/
```

### API Testing

```bash
# List models
curl http://localhost:8000/models

# Get stats
curl http://localhost:8000/stats

# Create model with ontology
curl -X POST http://localhost:8000/models \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GPT-Mini",
    "version": "1.0",
    "ontology": {
      "task_type": "text_generation",
      "input_schema": {"data_type": "text"},
      "output_schema": {"data_type": "text"}
    }
  }'
```

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.garden.yml
```

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.garden.yml logs backend

# Check container status
docker ps -a

# Rebuild from scratch
docker-compose -f docker-compose.garden.yml down
docker-compose -f docker-compose.garden.yml build --no-cache
docker-compose -f docker-compose.garden.yml up
```

### Frontend Can't Connect to Backend

Check `frontend/nginx.conf` - ensure proxy_pass points to correct service:

```nginx
location /api/ {
    proxy_pass http://backend:8000/;  # 'backend' is service name
}
```

### MLflow Data Not Persisting

Ensure volume mounts are correct:

```bash
# Check volumes
docker volume ls

# Inspect volume
docker volume inspect garden_mlruns
```

## 🚀 Production Deployment

### Build for Production

```bash
# Build optimized images
docker-compose -f docker-compose.garden.yml build

# Tag images
docker tag garden-backend:latest myregistry/garden-backend:v1.0
docker tag garden-frontend:latest myregistry/garden-frontend:v1.0

# Push to registry
docker push myregistry/garden-backend:v1.0
docker push myregistry/garden-frontend:v1.0
```

### Security Considerations

1. **Don't expose all ports** - Use reverse proxy (Nginx, Traefik)
2. **Add authentication** - Implement JWT or OAuth
3. **Use secrets** - Don't hardcode credentials
4. **Enable HTTPS** - Use Let's Encrypt or certificates
5. **Limit resources** - Add CPU/memory limits

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Production docker-compose

```yaml
version: '3.8'

services:
  backend:
    image: myregistry/garden-backend:v1.0
    restart: always
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
    # ... rest of config
```

## 📊 Monitoring

### Resource Usage

```bash
# All containers
docker stats

# Specific container
docker stats garden-backend
```

### Container Health

```bash
# Check health status
docker ps --filter "name=garden" --format "table {{.Names}}\t{{.Status}}"
```

## 🔄 Updates

### Update Services

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.garden.yml up -d --build

# Rolling update (zero downtime)
docker-compose -f docker-compose.garden.yml up -d --no-deps --build backend
```

## 📝 Summary

**One command to rule them all:**

```bash
docker-compose -f docker-compose.garden.yml up --build
```

Then access:
- **UI**: http://localhost:3000
- **API**: http://localhost:8000/docs
- **MLflow**: http://localhost:5000

**Data persists** across restarts in `./mlruns` and `./garden_data`.

**Clean slate:**

```bash
docker-compose -f docker-compose.garden.yml down -v
rm -rf mlruns/ garden_data/
```

🎉 **Your entire Garden platform is now containerized!**
