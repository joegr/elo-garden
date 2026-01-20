.PHONY: help build up down restart logs clean test

help:
	@echo "Model Arena Microservices - Make Commands"
	@echo ""
	@echo "  make build       - Build all Docker images"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View logs from all services"
	@echo "  make clean       - Remove all containers and volumes"
	@echo "  make test        - Run tests"
	@echo "  make init-db     - Initialize database"
	@echo "  make dev         - Run services in development mode"
	@echo ""

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services starting..."
	@echo "API Gateway: http://localhost:8000"
	@echo "Model Registry: http://localhost:8001"
	@echo "Arena Service: http://localhost:8002"
	@echo "Tournament Service: http://localhost:8003"
	@echo "Monitoring Service: http://localhost:8004"
	@echo "Team Service: http://localhost:8005"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	docker system prune -f

test:
	pytest tests/ -v

init-db:
	docker-compose exec postgres psql -U user -d model_arena -c "SELECT 1"
	@echo "Database initialized"

dev:
	@echo "Starting services in development mode..."
	@echo "Make sure PostgreSQL and Redis are running locally"
	@echo ""
	@echo "Run these commands in separate terminals:"
	@echo ""
	@echo "Terminal 1: cd services/model_registry && uvicorn app:app --reload --port 8001"
	@echo "Terminal 2: cd services/arena_service && uvicorn app:app --reload --port 8002"
	@echo "Terminal 3: cd services/tournament_service && uvicorn app:app --reload --port 8003"
	@echo "Terminal 4: cd services/monitoring_service && uvicorn app:app --reload --port 8004"
	@echo "Terminal 5: cd services/team_service && uvicorn app:app --reload --port 8005"
	@echo "Terminal 6: cd services/api_gateway && uvicorn app:app --reload --port 8000"

health:
	@curl -s http://localhost:8000/health | python -m json.tool

status:
	@docker-compose ps
