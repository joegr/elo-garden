from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import httpx

app = FastAPI(title="Arena Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ArenaType(str, Enum):
    BENCHMARK = "benchmark"
    CUSTOM = "custom"
    HUMAN_EVAL = "human_eval"

class ArenaStatus(str, Enum):
    AVAILABLE = "available"
    RENTED = "rented"
    MAINTENANCE = "maintenance"

class ArenaMetadata(BaseModel):
    arena_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    arena_type: ArenaType
    owner_team_id: Optional[str] = None
    rental_price_per_hour: float = 0.0
    status: ArenaStatus = ArenaStatus.AVAILABLE
    benchmark_config: Optional[Dict[str, Any]] = None
    evaluation_metrics: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    total_matches: int = 0
    tags: List[str] = []

class ArenaRental(BaseModel):
    rental_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    arena_id: str
    team_id: str
    start_time: datetime
    end_time: datetime
    total_cost: float
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.now)

class CreateArenaRequest(BaseModel):
    name: str
    description: str
    arena_type: ArenaType
    owner_team_id: str
    rental_price_per_hour: float = 0.0
    benchmark_config: Optional[Dict[str, Any]] = None
    evaluation_metrics: List[str] = []
    tags: List[str] = []

class RentArenaRequest(BaseModel):
    arena_id: str
    team_id: str
    duration_hours: int

class MatchRequest(BaseModel):
    arena_id: str
    model_a_id: str
    model_b_id: str
    benchmark_params: Optional[Dict[str, Any]] = None

arenas_db: Dict[str, ArenaMetadata] = {}
rentals_db: Dict[str, ArenaRental] = {}
matches_db: Dict[str, Dict[str, Any]] = {}

MODEL_REGISTRY_URL = "http://localhost:8001"

@app.get("/")
async def root():
    return {
        "service": "Arena Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/arenas", response_model=ArenaMetadata)
async def create_arena(request: CreateArenaRequest):
    arena_id = str(uuid.uuid4())
    
    arena = ArenaMetadata(
        arena_id=arena_id,
        name=request.name,
        description=request.description,
        arena_type=request.arena_type,
        owner_team_id=request.owner_team_id,
        rental_price_per_hour=request.rental_price_per_hour,
        benchmark_config=request.benchmark_config,
        evaluation_metrics=request.evaluation_metrics,
        tags=request.tags
    )
    
    arenas_db[arena_id] = arena
    return arena

@app.get("/arenas", response_model=List[ArenaMetadata])
async def list_arenas(
    status: Optional[ArenaStatus] = None,
    arena_type: Optional[ArenaType] = None,
    owner_team_id: Optional[str] = None
):
    filtered_arenas = list(arenas_db.values())
    
    if status:
        filtered_arenas = [a for a in filtered_arenas if a.status == status]
    if arena_type:
        filtered_arenas = [a for a in filtered_arenas if a.arena_type == arena_type]
    if owner_team_id:
        filtered_arenas = [a for a in filtered_arenas if a.owner_team_id == owner_team_id]
    
    return filtered_arenas

@app.get("/arenas/{arena_id}", response_model=ArenaMetadata)
async def get_arena(arena_id: str):
    if arena_id not in arenas_db:
        raise HTTPException(status_code=404, detail="Arena not found")
    return arenas_db[arena_id]

@app.post("/arenas/rent", response_model=ArenaRental)
async def rent_arena(request: RentArenaRequest):
    if request.arena_id not in arenas_db:
        raise HTTPException(status_code=404, detail="Arena not found")
    
    arena = arenas_db[request.arena_id]
    
    if arena.status != ArenaStatus.AVAILABLE:
        raise HTTPException(status_code=400, detail="Arena is not available for rent")
    
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=request.duration_hours)
    total_cost = arena.rental_price_per_hour * request.duration_hours
    
    rental = ArenaRental(
        arena_id=request.arena_id,
        team_id=request.team_id,
        start_time=start_time,
        end_time=end_time,
        total_cost=total_cost
    )
    
    rentals_db[rental.rental_id] = rental
    arena.status = ArenaStatus.RENTED
    arena.updated_at = datetime.now()
    
    return rental

@app.post("/arenas/rentals/{rental_id}/end")
async def end_rental(rental_id: str):
    if rental_id not in rentals_db:
        raise HTTPException(status_code=404, detail="Rental not found")
    
    rental = rentals_db[rental_id]
    rental.status = "completed"
    rental.end_time = datetime.now()
    
    arena = arenas_db[rental.arena_id]
    arena.status = ArenaStatus.AVAILABLE
    arena.updated_at = datetime.now()
    
    return {"message": "Rental ended successfully", "rental": rental}

@app.get("/arenas/rentals/team/{team_id}", response_model=List[ArenaRental])
async def get_team_rentals(team_id: str):
    team_rentals = [r for r in rentals_db.values() if r.team_id == team_id]
    return team_rentals

@app.post("/arenas/{arena_id}/matches")
async def run_match(arena_id: str, request: MatchRequest):
    if arena_id not in arenas_db:
        raise HTTPException(status_code=404, detail="Arena not found")
    
    arena = arenas_db[arena_id]
    match_id = str(uuid.uuid4())
    
    async with httpx.AsyncClient() as client:
        try:
            model_a_response = await client.get(f"{MODEL_REGISTRY_URL}/models/{request.model_a_id}")
            model_b_response = await client.get(f"{MODEL_REGISTRY_URL}/models/{request.model_b_id}")
            
            if model_a_response.status_code != 200 or model_b_response.status_code != 200:
                raise HTTPException(status_code=404, detail="One or both models not found")
            
            model_a = model_a_response.json()
            model_b = model_b_response.json()
            
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Model registry service unavailable: {str(e)}")
    
    match_data = {
        "match_id": match_id,
        "arena_id": arena_id,
        "model_a_id": request.model_a_id,
        "model_b_id": request.model_b_id,
        "model_a_name": model_a["name"],
        "model_b_name": model_b["name"],
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "benchmark_params": request.benchmark_params or arena.benchmark_config
    }
    
    matches_db[match_id] = match_data
    arena.total_matches += 1
    arena.updated_at = datetime.now()
    
    return match_data

@app.get("/arenas/{arena_id}/matches")
async def get_arena_matches(arena_id: str):
    if arena_id not in arenas_db:
        raise HTTPException(status_code=404, detail="Arena not found")
    
    arena_matches = [m for m in matches_db.values() if m["arena_id"] == arena_id]
    return arena_matches

@app.get("/matches/{match_id}")
async def get_match(match_id: str):
    if match_id not in matches_db:
        raise HTTPException(status_code=404, detail="Match not found")
    return matches_db[match_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
