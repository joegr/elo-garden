# Model Arena Microservices Platform

A comprehensive microservices architecture for AI model benchmarking with HuggingFace integration, performance monitoring, and team-based arena rental capabilities.

## Architecture Overview

The platform consists of 6 core microservices:

### 1. **API Gateway** (Port 8000)
- Central entry point for all client requests
- Request routing and load balancing
- Authentication and authorization
- Health monitoring of all services

### 2. **Model Registry Service** (Port 8001)
- Model registration and metadata management
- HuggingFace Hub integration
- Model loading and inference capabilities
- Performance metrics tracking per model

### 3. **Arena Service** (Port 8002)
- Arena creation and management
- Arena rental system for teams
- Match execution and coordination
- Support for multiple arena types (benchmark, custom, human_eval)

### 4. **Tournament Service** (Port 8003)
- Tournament creation and orchestration
- Multiple tournament formats (Round Robin, Single Elimination, Swiss)
- Automated match scheduling
- Real-time standings calculation

### 5. **Monitoring & Analytics Service** (Port 8004)
- Performance metrics collection
- Time-series data for model performance
- Global leaderboards
- Model comparison analytics
- Tournament statistics

### 6. **Team Management Service** (Port 8005)
- Team creation and member management
- Credit system for arena rentals
- Subscription tier management
- API key generation and authentication

## Technology Stack

- **Framework**: FastAPI (async Python web framework)
- **Database**: PostgreSQL (relational data)
- **Cache**: Redis (performance data, sessions)
- **ML Integration**: HuggingFace Transformers, PyTorch
- **Containerization**: Docker, Docker Compose
- **API Documentation**: OpenAPI/Swagger (auto-generated)

## Quick Start

### Prerequisites
- Docker and Docker Compose
- 8GB+ RAM recommended
- GPU optional (for model inference)

### Installation

1. Clone the repository:
```bash
cd /Users/jg/mind
```

2. Start all services:
```bash
docker-compose up -d
```

3. Verify services are running:
```bash
curl http://localhost:8000/health
```

4. Access API documentation:
- API Gateway: http://localhost:8000/docs
- Model Registry: http://localhost:8001/docs
- Arena Service: http://localhost:8002/docs
- Tournament Service: http://localhost:8003/docs
- Monitoring Service: http://localhost:8004/docs
- Team Service: http://localhost:8005/docs

### Running Services Locally (Development)

```bash
# Terminal 1 - Model Registry
cd services/model_registry
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 - Arena Service
cd services/arena_service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8002 --reload

# Terminal 3 - Tournament Service
cd services/tournament_service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8003 --reload

# Terminal 4 - Monitoring Service
cd services/monitoring_service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8004 --reload

# Terminal 5 - Team Service
cd services/team_service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8005 --reload

# Terminal 6 - API Gateway
cd services/api_gateway
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## API Usage Examples

### 1. Create a Team

```bash
curl -X POST "http://localhost:8005/teams" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI Research Lab",
    "description": "Our research team",
    "owner_email": "researcher@example.com"
  }'
```

### 2. Register a Model from HuggingFace

```bash
curl -X POST "http://localhost:8001/models/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GPT-2 Small",
    "team_id": "your-team-id",
    "huggingface_model_id": "gpt2",
    "version": "1.0.0",
    "description": "GPT-2 small model for testing",
    "tags": ["language-model", "gpt2"]
  }'
```

### 3. Create an Arena

```bash
curl -X POST "http://localhost:8002/arenas" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Text Generation Arena",
    "description": "Benchmark for text generation quality",
    "arena_type": "benchmark",
    "owner_team_id": "your-team-id",
    "rental_price_per_hour": 10.0,
    "evaluation_metrics": ["perplexity", "bleu", "rouge"],
    "tags": ["nlp", "generation"]
  }'
```

### 4. Rent an Arena

```bash
curl -X POST "http://localhost:8002/arenas/rent" \
  -H "Content-Type: application/json" \
  -d '{
    "arena_id": "arena-id",
    "team_id": "your-team-id",
    "duration_hours": 2
  }'
```

### 5. Create a Tournament

```bash
curl -X POST "http://localhost:8003/tournaments" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "LLM Championship 2024",
    "arena_id": "arena-id",
    "team_id": "your-team-id",
    "model_ids": ["model-1-id", "model-2-id", "model-3-id"],
    "tournament_type": "round_robin"
  }'
```

### 6. Start a Tournament

```bash
curl -X POST "http://localhost:8003/tournaments/{tournament-id}/start"
```

### 7. Get Tournament Standings

```bash
curl "http://localhost:8003/tournaments/{tournament-id}/standings"
```

### 8. Get Model Performance Metrics

```bash
curl "http://localhost:8004/metrics/model/{model-id}/performance"
```

### 9. Get Global Leaderboard

```bash
curl "http://localhost:8004/metrics/leaderboard?limit=10"
```

### 10. Compare Multiple Models

```bash
curl "http://localhost:8004/metrics/compare?model_ids=model-1-id,model-2-id,model-3-id"
```

## HuggingFace Integration

The Model Registry Service provides seamless integration with HuggingFace Hub:

### Supported Features

- **Model Discovery**: Search and browse HuggingFace models
- **Automatic Loading**: Load models directly from HuggingFace Hub
- **Config Extraction**: Automatically extract model architecture details
- **Inference**: Run inference on loaded models
- **Quantization**: Support for 8-bit and 4-bit quantization
- **Multi-GPU**: Automatic device mapping for large models

### Example: Load and Use a HuggingFace Model

```python
from services.model_registry.huggingface_client import HuggingFaceClient, ModelLoadConfig

# Initialize client
hf_client = HuggingFaceClient(cache_dir="/path/to/cache")

# Load model
config = ModelLoadConfig(
    model_id="gpt2",
    device="auto",
    torch_dtype="float16",
    load_in_8bit=False
)

model = hf_client.load_model(config)
tokenizer = hf_client.load_tokenizer("gpt2")

# Generate text
outputs = hf_client.generate_text(
    model_id="gpt2",
    prompt="The future of AI is",
    max_length=100,
    temperature=0.8
)
```

## Performance Monitoring

The Monitoring Service tracks comprehensive metrics:

### Model-Level Metrics
- Total matches played
- Win/loss/draw statistics
- Win rate over time
- Performance trends (improving/stable/declining)
- Average scores across benchmarks

### Tournament-Level Metrics
- Match completion statistics
- Model rankings and standings
- Duration and timing data

### Time-Series Data
- Performance evolution over time
- Configurable time windows (7, 30, 90 days)
- Exportable for external analysis

## Arena Rental System

Teams can rent arenas for exclusive benchmarking:

### Rental Features
- Hourly pricing model
- Automatic credit deduction
- Rental status tracking
- Multi-team support
- Flexible duration

### Subscription Tiers
- **Free**: Limited credits, basic features
- **Basic**: More credits, priority support
- **Pro**: Unlimited credits, advanced analytics
- **Enterprise**: Custom solutions, dedicated support

## Database Schema

The platform uses PostgreSQL with the following main tables:

- `teams`: Team information and credits
- `users`: User accounts and API keys
- `models`: Model registry and metadata
- `arenas`: Arena configurations
- `arena_rentals`: Rental transactions
- `tournaments`: Tournament data
- `matches`: Individual match results
- `match_metrics`: Detailed performance metrics

## Security

- API key authentication for all services
- Team-based access control
- Rate limiting (configurable)
- Encrypted credentials storage
- Audit logging for all operations

## Scaling Considerations

### Horizontal Scaling
- Each service can be scaled independently
- Load balancer in front of API Gateway
- Database read replicas for analytics

### Vertical Scaling
- Model Registry: GPU instances for inference
- Monitoring Service: More memory for time-series data
- Database: Larger instances for high-throughput

## Monitoring & Observability

### Health Checks
```bash
curl http://localhost:8000/health
```

### Service Logs
```bash
docker-compose logs -f [service-name]
```

### Metrics
- Request latency per endpoint
- Service availability
- Database connection pool stats
- Model inference times

## Development

### Adding a New Service

1. Create service directory: `services/new_service/`
2. Add `app.py`, `requirements.txt`, `Dockerfile`
3. Update `docker-compose.yml`
4. Update API Gateway routing
5. Add tests and documentation

### Running Tests

```bash
# Unit tests
pytest services/model_registry/tests/

# Integration tests
pytest tests/integration/

# Load tests
locust -f tests/load/locustfile.py
```

## Troubleshooting

### Services won't start
```bash
docker-compose down -v
docker-compose up --build
```

### Database connection issues
```bash
docker-compose exec postgres psql -U user -d model_arena
```

### Model loading fails
- Check HuggingFace Hub connectivity
- Verify model ID is correct
- Ensure sufficient disk space for model cache
- Check GPU availability for large models

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

- Documentation: http://localhost:8000/docs
- Issues: GitHub Issues
- Email: support@modelarena.ai
