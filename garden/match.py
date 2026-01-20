from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class MatchStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MatchResult:
    def __init__(
        self,
        match_id: str,
        winner_id: Optional[str],
        scores: Dict[str, float],
        rating_changes: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.match_id = match_id
        self.winner_id = winner_id
        self.scores = scores
        self.rating_changes = rating_changes
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'match_id': self.match_id,
            'winner_id': self.winner_id,
            'scores': self.scores,
            'rating_changes': self.rating_changes,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


class Match:
    def __init__(
        self,
        model_a_id: str,
        model_b_id: str,
        arena_id: str,
        match_id: Optional[str] = None,
        tournament_id: Optional[str] = None,
        season_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.match_id = match_id or str(uuid.uuid4())
        self.model_a_id = model_a_id
        self.model_b_id = model_b_id
        self.arena_id = arena_id
        self.tournament_id = tournament_id
        self.season_id = season_id
        self.metadata = metadata or {}
        
        self.status = MatchStatus.PENDING
        self.result: Optional[MatchResult] = None
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
    
    def start(self):
        self.status = MatchStatus.IN_PROGRESS
        self.started_at = datetime.now()
    
    def complete(self, result: MatchResult):
        self.status = MatchStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now()
    
    def cancel(self):
        self.status = MatchStatus.CANCELLED
        self.completed_at = datetime.now()
    
    def get_participants(self) -> List[str]:
        return [self.model_a_id, self.model_b_id]
    
    def __repr__(self) -> str:
        return f"Match(id={self.match_id}, {self.model_a_id} vs {self.model_b_id}, status={self.status.value})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'match_id': self.match_id,
            'model_a_id': self.model_a_id,
            'model_b_id': self.model_b_id,
            'arena_id': self.arena_id,
            'tournament_id': self.tournament_id,
            'season_id': self.season_id,
            'status': self.status.value,
            'result': self.result.to_dict() if self.result else None,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata': self.metadata
        }
