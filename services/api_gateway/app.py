from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import httpx
from datetime import datetime
import logging

app = FastAPI(title="API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICES = {
    "model_registry": "http://localhost:8001",
    "arena_service": "http://localhost:8002",
    "tournament_service": "http://localhost:8003",
    "monitoring_service": "http://localhost:8004",
    "team_service": "http://localhost:8005"
}

@app.get("/")
async def root():
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "status": "running",
        "services": list(SERVICES.keys())
    }

@app.get("/health")
async def health_check():
    service_status = {}
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, service_url in SERVICES.items():
            try:
                response = await client.get(f"{service_url}/")
                service_status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            except Exception as e:
                service_status[service_name] = {
                    "status": "unreachable",
                    "error": str(e)
                }
    
    all_healthy = all(s["status"] == "healthy" for s in service_status.values())
    
    return {
        "gateway_status": "healthy" if all_healthy else "degraded",
        "services": service_status,
        "timestamp": datetime.now().isoformat()
    }

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    api_key = credentials.credentials
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{SERVICES['team_service']}/teams",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if response.status_code == 200:
                return api_key
        except Exception:
            pass
    
    raise HTTPException(status_code=401, detail="Invalid API key")

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(
    service: str,
    path: str,
    request: Request
):
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")
    
    service_url = SERVICES[service]
    target_url = f"{service_url}/{path}"
    
    logger.info(f"Proxying {request.method} request to {target_url}")
    
    headers = dict(request.headers)
    headers.pop("host", None)
    
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=body
            )
            
            return response.json() if response.headers.get("content-type") == "application/json" else response.text
            
        except httpx.RequestError as e:
            logger.error(f"Error proxying request to {service}: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Service '{service}' unavailable")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/models")
async def list_all_models():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICES['model_registry']}/models")
        return response.json()

@app.get("/api/arenas")
async def list_all_arenas():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICES['arena_service']}/arenas")
        return response.json()

@app.get("/api/tournaments")
async def list_all_tournaments():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SERVICES['tournament_service']}/tournaments")
        return response.json()

@app.get("/api/leaderboard")
async def get_leaderboard(limit: int = 10):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SERVICES['monitoring_service']}/metrics/leaderboard",
            params={"limit": limit}
        )
        return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
