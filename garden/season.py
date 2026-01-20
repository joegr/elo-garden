from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class SeasonStatus(Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Season:
    def __init__(
        self,
        name: str,
        arena_ids: List[str],
        season_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.season_id = season_id or str(uuid.uuid4())
        self.name = name
        self.arena_ids = arena_ids
        self.start_date = start_date or datetime.now()
        self.end_date = end_date
        self.metadata = metadata or {}
        
        self.status = SeasonStatus.SCHEDULED
        self.tournament_ids: List[str] = []
        self.match_ids: List[str] = []
        self.participating_model_ids: List[str] = []
        
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        
        self.arena_ratings: Dict[str, Dict[str, float]] = {}
        for arena_id in arena_ids:
            self.arena_ratings[arena_id] = {}
    
    def start(self):
        self.status = SeasonStatus.ACTIVE
        self.start_date = datetime.now()
    
    def complete(self):
        self.status = SeasonStatus.COMPLETED
        self.completed_at = datetime.now()
        if not self.end_date:
            self.end_date = self.completed_at
    
    def cancel(self):
        self.status = SeasonStatus.CANCELLED
        self.completed_at = datetime.now()
    
    def add_tournament(self, tournament_id: str):
        if tournament_id not in self.tournament_ids:
            self.tournament_ids.append(tournament_id)
    
    def add_match(self, match_id: str):
        if match_id not in self.match_ids:
            self.match_ids.append(match_id)
    
    def register_model(self, model_id: str):
        if model_id not in self.participating_model_ids:
            self.participating_model_ids.append(model_id)
            
            for arena_id in self.arena_ids:
                if model_id not in self.arena_ratings[arena_id]:
                    self.arena_ratings[arena_id][model_id] = 1500
    
    def update_rating(self, arena_id: str, model_id: str, new_rating: float):
        if arena_id in self.arena_ratings:
            self.arena_ratings[arena_id][model_id] = new_rating
    
    def get_rating(self, arena_id: str, model_id: str, default: float = 1500) -> float:
        if arena_id in self.arena_ratings:
            return self.arena_ratings[arena_id].get(model_id, default)
        return default
    
    def get_arena_leaderboard(self, arena_id: str) -> List[Tuple[str, float]]:
        if arena_id not in self.arena_ratings:
            return []
        
        return sorted(
            self.arena_ratings[arena_id].items(),
            key=lambda x: x[1],
            reverse=True
        )
    
    def get_overall_leaderboard(self) -> List[Tuple[str, float]]:
        overall_ratings = {}
        
        for model_id in self.participating_model_ids:
            total_rating = 0
            count = 0
            
            for arena_id in self.arena_ids:
                if model_id in self.arena_ratings[arena_id]:
                    total_rating += self.arena_ratings[arena_id][model_id]
                    count += 1
            
            if count > 0:
                overall_ratings[model_id] = total_rating / count
        
        return sorted(
            overall_ratings.items(),
            key=lambda x: x[1],
            reverse=True
        )
    
    def __repr__(self) -> str:
        return f"Season(id={self.season_id}, name={self.name}, status={self.status.value})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'season_id': self.season_id,
            'name': self.name,
            'arena_ids': self.arena_ids,
            'status': self.status.value,
            'tournament_ids': self.tournament_ids,
            'match_ids': self.match_ids,
            'participating_model_ids': self.participating_model_ids,
            'arena_ratings': self.arena_ratings,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata': self.metadata
        }
