"""
Garden REST API - FastAPI Backend

Provides REST endpoints for the Garden UI to interact with the backend
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from garden import Garden, TournamentType
from garden.ontology import ModelOntology, OntologyMatcher, IOSchema, DataType, TaskType
from garden.arena_queue import ArenaQueue, QueueStatus

# Initialize FastAPI app
app = FastAPI(
    title="Garden API",
    description="Model Arena and Experiment Management",
    version="0.3.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Garden instance with SQLite persistence
garden = Garden(
    name="API Garden",
    data_dir="garden_data",
    db_path="garden_data/garden.db"
)

# Global ArenaQueue instance
arena_queue = ArenaQueue()

# Ontology will be stored in Model.ontology


# Pydantic models for API
class ModelCreate(BaseModel):
    name: str
    version: str = "1.0"
    metadata: Optional[Dict[str, Any]] = None
    ontology: Optional[Dict[str, Any]] = None


class ModelResponse(BaseModel):
    model_id: str
    name: str
    version: str
    metadata: Dict[str, Any]
    ratings: Dict[str, float]
    stats: Dict[str, Any]
    ontology: Optional[Dict[str, Any]] = None
    average_rating: Optional[float] = None
    highest_rating: Optional[float] = None


class ArenaCreate(BaseModel):
    name: str
    description: Optional[str] = None
    higher_is_better: bool = True


class ArenaResponse(BaseModel):
    arena_id: str
    name: str
    description: Optional[str]
    match_count: int


class MatchCreate(BaseModel):
    model_a_id: str
    model_b_id: str
    arena_id: str


class MatchResponse(BaseModel):
    match_id: str
    model_a_id: str
    model_b_id: str
    arena_id: str
    winner_id: Optional[str]
    scores: Dict[str, float]
    rating_changes: Dict[str, float]


class TournamentCreate(BaseModel):
    name: str
    arena_id: str
    model_ids: List[str]
    tournament_type: str = "ROUND_ROBIN"


class CompatibilityRequest(BaseModel):
    model_id: str
    min_score: float = 0.5


class CompatibilityResponse(BaseModel):
    model_id: str
    model_name: str
    compatibility_score: float
    ontology: Dict[str, Any]


class OntologyUpdate(BaseModel):
    ontology: Optional[Dict[str, Any]] = None
    changed_by: Optional[str] = None
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class QueueMatchRequest(BaseModel):
    model_a_id: str
    model_b_id: str
    arena_id: str
    priority: int = 0
    metadata: Optional[Dict[str, Any]] = None


# API Endpoints

@app.get("/")
async def root():
    """Health check"""
    stats = garden.get_stats()
    return {
        "status": "healthy",
        "service": "Garden API",
        "version": "0.4.0",
        "models": stats['total_models'],
        "arenas": stats['total_arenas'],
        "matches": stats['total_matches']
    }


@app.get("/models", response_model=List[ModelResponse])
async def list_models():
    """Get all registered models with ELO ratings"""
    models = []
    for model in garden.models.values():
        # Calculate average and highest ELO
        ratings_list = list(model.ratings.values())
        avg_rating = sum(ratings_list) / len(ratings_list) if ratings_list else garden.elo_system.initial_rating
        high_rating = max(ratings_list) if ratings_list else garden.elo_system.initial_rating
        
        models.append(ModelResponse(
            model_id=model.model_id,
            name=model.name,
            version=model.version,
            metadata=model.metadata,
            ratings=model.ratings,
            stats=model.stats,
            ontology=model.ontology.to_dict() if model.ontology else None,
            average_rating=avg_rating,
            highest_rating=high_rating
        ))
    return models


@app.post("/models", response_model=ModelResponse)
async def create_model(model_data: ModelCreate):
    """Register a new model"""
    # Create ontology if provided
    ontology = None
    if model_data.ontology:
        try:
            ontology = ModelOntology.from_dict(model_data.ontology)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid ontology: {str(e)}")
    
    # Register model with ontology
    model = garden.register_model(
        name=model_data.name,
        version=model_data.version,
        metadata=model_data.metadata,
        ontology=ontology
    )
    
    # Update ontology model_id after model creation
    if model.ontology:
        model.ontology.model_id = model.model_id
    
    return ModelResponse(
        model_id=model.model_id,
        name=model.name,
        version=model.version,
        metadata=model.metadata,
        ratings=model.ratings,
        stats=model.stats,
        ontology=model.ontology.to_dict() if model.ontology else None
    )


@app.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str):
    """Get a specific model"""
    if model_id not in garden.models:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model = garden.models[model_id]
    return ModelResponse(
        model_id=model.model_id,
        name=model.name,
        version=model.version,
        metadata=model.metadata,
        ratings=model.ratings,
        stats=model.stats,
        ontology=model.ontology.to_dict() if model.ontology else None
    )


@app.put("/models/{model_id}/ontology")
async def update_model_ontology(model_id: str, update: OntologyUpdate):
    """Update a model's ontology"""
    if model_id not in garden.models:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model = garden.models[model_id]
    
    # Create new ontology if provided
    new_ontology = None
    if update.ontology:
        try:
            new_ontology = ModelOntology.from_dict(update.ontology)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid ontology: {str(e)}")
    
    # Update the ontology
    model.update_ontology(
        new_ontology=new_ontology,
        changed_by=update.changed_by,
        reason=update.reason,
        metadata=update.metadata
    )
    
    return {
        "message": "Ontology updated successfully",
        "model_id": model_id,
        "ontology": model.ontology.to_dict() if model.ontology else None,
        "history_count": model.ontology_history.count()
    }


@app.get("/models/{model_id}/ontology/history")
async def get_ontology_history(model_id: str):
    """Get the ontology change history for a model"""
    if model_id not in garden.models:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model = garden.models[model_id]
    return model.ontology_history.to_dict()


@app.post("/models/{model_id}/compatible", response_model=List[CompatibilityResponse])
async def get_compatible_models(
    model_id: str,
    request: CompatibilityRequest,
    arena_id: Optional[str] = None,
    use_elo: bool = True
):
    """
    Find models compatible with the given model based on ontology and ELO ratings
    
    Args:
        model_id: Target model ID
        request: Compatibility request with min_score
        arena_id: Arena to get ELO ratings from (optional)
        use_elo: Whether to include ELO proximity in matching (default: True)
    """
    if model_id not in garden.models:
        raise HTTPException(status_code=404, detail="Model not found")
    
    target_model = garden.models[model_id]
    if not target_model.ontology:
        raise HTTPException(status_code=400, detail="Model does not have ontology for compatibility matching")
    
    target_ontology = target_model.ontology
    candidate_ontologies = [m.ontology for m in garden.models.values() if m.ontology and m.model_id != model_id]
    
    # Get ELO ratings if requested
    target_rating = None
    candidate_ratings = {}
    
    if use_elo and model_id in garden.models:
        target_model = garden.models[model_id]
        if arena_id:
            target_rating = target_model.get_rating(arena_id, garden.elo_system.initial_rating)
        else:
            # Use average rating across all arenas
            ratings = list(target_model.ratings.values())
            target_rating = sum(ratings) / len(ratings) if ratings else garden.elo_system.initial_rating
        
        # Get candidate ratings
        for ont in candidate_ontologies:
            if ont.model_id in garden.models:
                model = garden.models[ont.model_id]
                if arena_id:
                    candidate_ratings[ont.model_id] = model.get_rating(arena_id, garden.elo_system.initial_rating)
                else:
                    ratings = list(model.ratings.values())
                    candidate_ratings[ont.model_id] = sum(ratings) / len(ratings) if ratings else garden.elo_system.initial_rating
    
    compatible = OntologyMatcher.find_compatible_models(
        target_ontology,
        candidate_ontologies,
        target_rating=target_rating,
        candidate_ratings=candidate_ratings,
        min_score=request.min_score,
        elo_weight=0.3,
        prefer_close_ratings=use_elo
    )
    
    results = []
    for ont, score in compatible:
        model = garden.models.get(ont.model_id)
        if model:
            # Get model's ELO rating for response
            if arena_id:
                elo_rating = model.get_rating(arena_id, garden.elo_system.initial_rating)
            else:
                ratings = list(model.ratings.values())
                elo_rating = sum(ratings) / len(ratings) if ratings else garden.elo_system.initial_rating
            
            results.append(CompatibilityResponse(
                model_id=ont.model_id,
                model_name=model.name,
                compatibility_score=score,
                ontology=ont.to_dict()
            ))
    
    return results


@app.get("/models/elo/leaderboard")
async def get_elo_leaderboard(arena_id: Optional[str] = None, top_n: int = 10):
    """Get top models by ELO rating"""
    return garden.get_elo_leaderboard(arena_id=arena_id, top_n=top_n)


@app.get("/models/elo/range")
async def get_models_by_elo(
    arena_id: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None
):
    """Get models within a specific ELO rating range"""
    models = garden.get_models_by_elo_range(
        arena_id=arena_id,
        min_rating=min_rating,
        max_rating=max_rating
    )
    
    return [
        {
            'model_id': m.model_id,
            'name': m.name,
            'version': m.version,
            'rating': m.get_rating(arena_id, garden.elo_system.initial_rating) if arena_id else (
                sum(m.ratings.values()) / len(m.ratings.values()) if m.ratings.values() else garden.elo_system.initial_rating
            ),
            'stats': m.stats
        }
        for m in models
    ]


@app.get("/models/{model_id}/best-opponent")
async def find_best_opponent(
    model_id: str,
    arena_id: Optional[str] = None,
    rating_tolerance: float = 200
):
    """Find the best opponent for a model based on ELO proximity"""
    opponent = garden.find_best_matchup(
        model_id=model_id,
        arena_id=arena_id,
        rating_tolerance=rating_tolerance
    )
    
    if not opponent:
        raise HTTPException(status_code=404, detail="No suitable opponent found")
    
    return {
        'model_id': opponent.model_id,
        'name': opponent.name,
        'version': opponent.version,
        'rating': opponent.get_rating(arena_id, garden.elo_system.initial_rating) if arena_id else (
            sum(opponent.ratings.values()) / len(opponent.ratings.values()) if opponent.ratings.values() else garden.elo_system.initial_rating
        ),
        'stats': opponent.stats
    }


@app.get("/arenas", response_model=List[ArenaResponse])
async def list_arenas():
    """Get all arenas"""
    arenas = []
    for arena in garden.arenas.values():
        arenas.append(ArenaResponse(
            arena_id=arena.arena_id,
            name=arena.name,
            description=arena.description,
            match_count=len(arena.match_history)
        ))
    return arenas


@app.post("/arenas", response_model=ArenaResponse)
async def create_arena(arena_data: ArenaCreate):
    """Create a new arena"""
    # For API, we'll create a simple benchmark arena
    # In production, you'd want to support custom benchmark functions
    def default_benchmark(model, **kwargs):
        import random
        return random.uniform(0.5, 1.0)
    
    arena = garden.create_benchmark_arena(
        name=arena_data.name,
        benchmark_fn=default_benchmark,
        description=arena_data.description,
        higher_is_better=arena_data.higher_is_better
    )
    
    return ArenaResponse(
        arena_id=arena.arena_id,
        name=arena.name,
        description=arena.description,
        match_count=0
    )


@app.post("/matches", response_model=MatchResponse)
async def create_match(match_data: MatchCreate, background_tasks: BackgroundTasks):
    """Run a match between two models immediately"""
    if match_data.model_a_id not in garden.models:
        raise HTTPException(status_code=404, detail=f"Model {match_data.model_a_id} not found")
    
    if match_data.model_b_id not in garden.models:
        raise HTTPException(status_code=404, detail=f"Model {match_data.model_b_id} not found")
    
    if match_data.arena_id not in garden.arenas:
        raise HTTPException(status_code=404, detail=f"Arena {match_data.arena_id} not found")
    
    # Run the match
    match = garden.run_match(
        model_a_id=match_data.model_a_id,
        model_b_id=match_data.model_b_id,
        arena_id=match_data.arena_id
    )
    
    return MatchResponse(
        match_id=match.match_id,
        model_a_id=match.model_a_id,
        model_b_id=match.model_b_id,
        arena_id=match.arena_id,
        winner_id=match.result.winner_id if match.result else None,
        scores=match.result.scores if match.result else {},
        rating_changes=match.result.rating_changes if match.result else {}
    )


# Queue Endpoints

@app.post("/queue/matches")
async def queue_match(request: QueueMatchRequest):
    """Add a match to the queue"""
    if request.model_a_id not in garden.models:
        raise HTTPException(status_code=404, detail=f"Model {request.model_a_id} not found")
    
    if request.model_b_id not in garden.models:
        raise HTTPException(status_code=404, detail=f"Model {request.model_b_id} not found")
    
    if request.arena_id not in garden.arenas:
        raise HTTPException(status_code=404, detail=f"Arena {request.arena_id} not found")
    
    queued_match = arena_queue.add_match(
        model_a_id=request.model_a_id,
        model_b_id=request.model_b_id,
        arena_id=request.arena_id,
        priority=request.priority,
        metadata=request.metadata
    )
    
    return queued_match.to_dict()


@app.get("/queue/status")
async def get_queue_status():
    """Get overall queue status"""
    return arena_queue.get_queue_status()


@app.get("/queue/matches")
async def get_queued_matches():
    """Get all queued matches"""
    return arena_queue.get_all_queued()


@app.get("/queue/history")
async def get_queue_history(limit: int = 20):
    """Get queue history"""
    return arena_queue.get_history(limit=limit)


@app.get("/queue/matches/{queue_id}")
async def get_queued_match(queue_id: str):
    """Get a specific queued match"""
    match = arena_queue.get_by_id(queue_id)
    if not match:
        raise HTTPException(status_code=404, detail="Queued match not found")
    return match.to_dict()


@app.delete("/queue/matches/{queue_id}")
async def cancel_queued_match(queue_id: str):
    """Cancel a queued match"""
    success = arena_queue.cancel_match(queue_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel match (not found or already started)")
    return {"message": "Match cancelled", "queue_id": queue_id}


@app.post("/queue/process")
async def process_queue(background_tasks: BackgroundTasks, max_matches: int = 1):
    """Process matches from the queue"""
    processed = []
    
    for _ in range(max_matches):
        queued_match = arena_queue.get_next()
        if not queued_match:
            break
        
        # Start the match
        arena_queue.start_match(queued_match.queue_id)
        
        try:
            # Run the match
            match = garden.run_match(
                model_a_id=queued_match.model_a_id,
                model_b_id=queued_match.model_b_id,
                arena_id=queued_match.arena_id
            )
            
            # Mark as completed
            arena_queue.complete_match(
                queue_id=queued_match.queue_id,
                match_id=match.match_id,
                result={
                    'winner_id': match.result.winner_id if match.result else None,
                    'scores': match.result.scores if match.result else {},
                    'rating_changes': match.result.rating_changes if match.result else {}
                }
            )
            
            processed.append({
                'queue_id': queued_match.queue_id,
                'match_id': match.match_id,
                'status': 'completed'
            })
            
        except Exception as e:
            # Mark as failed
            arena_queue.fail_match(queued_match.queue_id, str(e))
            processed.append({
                'queue_id': queued_match.queue_id,
                'status': 'failed',
                'error': str(e)
            })
    
    return {
        'processed': len(processed),
        'matches': processed
    }


@app.delete("/queue/clear")
async def clear_queue():
    """Clear all pending matches from queue"""
    arena_queue.clear_queue()
    return {"message": "Queue cleared"}


@app.post("/tournaments")
async def create_tournament(tournament_data: TournamentCreate):
    """Create and run a tournament"""
    if tournament_data.arena_id not in garden.arenas:
        raise HTTPException(status_code=404, detail="Arena not found")
    
    for model_id in tournament_data.model_ids:
        if model_id not in garden.models:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    
    try:
        tournament_type = TournamentType[tournament_data.tournament_type.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid tournament type")
    
    tournament = garden.create_tournament(
        name=tournament_data.name,
        arena_id=tournament_data.arena_id,
        model_ids=tournament_data.model_ids,
        tournament_type=tournament_type
    )
    
    # Run tournament in background
    garden.run_tournament(tournament.tournament_id)
    
    return {
        "tournament_id": tournament.tournament_id,
        "name": tournament.name,
        "status": tournament.status.value,
        "match_count": len(tournament.match_ids)
    }


@app.get("/stats")
async def get_stats():
    """Get Garden statistics"""
    return garden.get_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
