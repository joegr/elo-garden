from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid
import httpx
import asyncio

app = FastAPI(title="Tournament Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TournamentType(str, Enum):
    ROUND_ROBIN = "round_robin"
    SINGLE_ELIMINATION = "single_elimination"
    SWISS = "swiss"

class TournamentStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TournamentMetadata(BaseModel):
    tournament_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    arena_id: str
    team_id: str
    model_ids: List[str]
    tournament_type: TournamentType
    status: TournamentStatus = TournamentStatus.SCHEDULED
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    standings: Dict[str, Dict[str, Any]] = {}
    match_ids: List[str] = []
    current_round: int = 0
    total_rounds: int = 0

class CreateTournamentRequest(BaseModel):
    name: str
    arena_id: str
    team_id: str
    model_ids: List[str]
    tournament_type: TournamentType = TournamentType.ROUND_ROBIN

tournaments_db: Dict[str, TournamentMetadata] = {}

ARENA_SERVICE_URL = "http://localhost:8002"
MONITORING_SERVICE_URL = "http://localhost:8004"

@app.get("/")
async def root():
    return {
        "service": "Tournament Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/tournaments", response_model=TournamentMetadata)
async def create_tournament(request: CreateTournamentRequest):
    if len(request.model_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 models required for tournament")
    
    tournament_id = str(uuid.uuid4())
    
    standings = {}
    for model_id in request.model_ids:
        standings[model_id] = {
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "points": 0,
            "matches_played": 0
        }
    
    total_rounds = 1
    if request.tournament_type == TournamentType.ROUND_ROBIN:
        total_rounds = len(request.model_ids) - 1
    elif request.tournament_type == TournamentType.SWISS:
        total_rounds = min(len(request.model_ids) - 1, 5)
    
    tournament = TournamentMetadata(
        tournament_id=tournament_id,
        name=request.name,
        arena_id=request.arena_id,
        team_id=request.team_id,
        model_ids=request.model_ids,
        tournament_type=request.tournament_type,
        standings=standings,
        total_rounds=total_rounds
    )
    
    tournaments_db[tournament_id] = tournament
    return tournament

@app.get("/tournaments", response_model=List[TournamentMetadata])
async def list_tournaments(
    team_id: Optional[str] = None,
    status: Optional[TournamentStatus] = None,
    arena_id: Optional[str] = None
):
    filtered_tournaments = list(tournaments_db.values())
    
    if team_id:
        filtered_tournaments = [t for t in filtered_tournaments if t.team_id == team_id]
    if status:
        filtered_tournaments = [t for t in filtered_tournaments if t.status == status]
    if arena_id:
        filtered_tournaments = [t for t in filtered_tournaments if t.arena_id == arena_id]
    
    return filtered_tournaments

@app.get("/tournaments/{tournament_id}", response_model=TournamentMetadata)
async def get_tournament(tournament_id: str):
    if tournament_id not in tournaments_db:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournaments_db[tournament_id]

@app.post("/tournaments/{tournament_id}/start")
async def start_tournament(tournament_id: str, background_tasks: BackgroundTasks):
    if tournament_id not in tournaments_db:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    tournament = tournaments_db[tournament_id]
    
    if tournament.status != TournamentStatus.SCHEDULED:
        raise HTTPException(status_code=400, detail="Tournament already started or completed")
    
    tournament.status = TournamentStatus.IN_PROGRESS
    tournament.started_at = datetime.now()
    
    background_tasks.add_task(run_tournament_matches, tournament_id)
    
    return {"message": "Tournament started", "tournament_id": tournament_id}

async def run_tournament_matches(tournament_id: str):
    tournament = tournaments_db[tournament_id]
    
    matches = generate_matches(tournament)
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        for model_a_id, model_b_id in matches:
            try:
                response = await client.post(
                    f"{ARENA_SERVICE_URL}/arenas/{tournament.arena_id}/matches",
                    json={
                        "arena_id": tournament.arena_id,
                        "model_a_id": model_a_id,
                        "model_b_id": model_b_id
                    }
                )
                
                if response.status_code == 200:
                    match_data = response.json()
                    tournament.match_ids.append(match_data["match_id"])
                    
                    await asyncio.sleep(1)
                    
                    winner = await simulate_match_result(model_a_id, model_b_id)
                    update_standings(tournament, model_a_id, model_b_id, winner)
                    
                    await report_match_to_monitoring(tournament_id, match_data["match_id"], model_a_id, model_b_id, winner)
                    
            except Exception as e:
                print(f"Error running match: {str(e)}")
                continue
    
    tournament.status = TournamentStatus.COMPLETED
    tournament.completed_at = datetime.now()
    tournament.current_round = tournament.total_rounds

def generate_matches(tournament: TournamentMetadata) -> List[tuple]:
    if tournament.tournament_type == TournamentType.ROUND_ROBIN:
        matches = []
        for i, model_a in enumerate(tournament.model_ids):
            for model_b in tournament.model_ids[i+1:]:
                matches.append((model_a, model_b))
        return matches
    elif tournament.tournament_type == TournamentType.SINGLE_ELIMINATION:
        import random
        models = tournament.model_ids.copy()
        random.shuffle(models)
        matches = []
        for i in range(0, len(models) - 1, 2):
            matches.append((models[i], models[i+1]))
        return matches
    else:
        return []

async def simulate_match_result(model_a_id: str, model_b_id: str) -> str:
    import random
    result = random.choice(["model_a", "model_b", "draw"])
    return result

def update_standings(tournament: TournamentMetadata, model_a_id: str, model_b_id: str, winner: str):
    tournament.standings[model_a_id]["matches_played"] += 1
    tournament.standings[model_b_id]["matches_played"] += 1
    
    if winner == "model_a":
        tournament.standings[model_a_id]["wins"] += 1
        tournament.standings[model_a_id]["points"] += 3
        tournament.standings[model_b_id]["losses"] += 1
    elif winner == "model_b":
        tournament.standings[model_b_id]["wins"] += 1
        tournament.standings[model_b_id]["points"] += 3
        tournament.standings[model_a_id]["losses"] += 1
    else:
        tournament.standings[model_a_id]["draws"] += 1
        tournament.standings[model_a_id]["points"] += 1
        tournament.standings[model_b_id]["draws"] += 1
        tournament.standings[model_b_id]["points"] += 1

async def report_match_to_monitoring(tournament_id: str, match_id: str, model_a_id: str, model_b_id: str, winner: str):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{MONITORING_SERVICE_URL}/metrics/match",
                json={
                    "tournament_id": tournament_id,
                    "match_id": match_id,
                    "model_a_id": model_a_id,
                    "model_b_id": model_b_id,
                    "winner": winner,
                    "timestamp": datetime.now().isoformat()
                }
            )
    except Exception as e:
        print(f"Failed to report to monitoring service: {str(e)}")

@app.get("/tournaments/{tournament_id}/standings")
async def get_tournament_standings(tournament_id: str):
    if tournament_id not in tournaments_db:
        raise HTTPException(status_code=404, detail="Tournament not found")
    
    tournament = tournaments_db[tournament_id]
    
    sorted_standings = sorted(
        tournament.standings.items(),
        key=lambda x: (x[1]["points"], x[1]["wins"]),
        reverse=True
    )
    
    return {
        "tournament_id": tournament_id,
        "standings": sorted_standings,
        "status": tournament.status
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
