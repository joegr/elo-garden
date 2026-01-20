from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class Model:
    def __init__(
        self,
        name: str,
        model_id: Optional[str] = None,
        version: str = "1.0",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.model_id = model_id or str(uuid.uuid4())
        self.name = name
        self.version = version
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        
        self.ratings: Dict[str, float] = {}
        self.match_history: List[str] = []
        self.stats: Dict[str, Any] = {
            'total_matches': 0,
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'win_rate': 0.0
        }
    
    def get_rating(self, arena_id: str, default: float = 1500) -> float:
        return self.ratings.get(arena_id, default)
    
    def set_rating(self, arena_id: str, rating: float):
        self.ratings[arena_id] = rating
    
    def update_stats(self, result: str):
        self.stats['total_matches'] += 1
        
        if result == 'win':
            self.stats['wins'] += 1
        elif result == 'loss':
            self.stats['losses'] += 1
        elif result == 'draw':
            self.stats['draws'] += 1
        
        if self.stats['total_matches'] > 0:
            self.stats['win_rate'] = self.stats['wins'] / self.stats['total_matches']
    
    def add_match(self, match_id: str):
        self.match_history.append(match_id)
    
    def __repr__(self) -> str:
        return f"Model(id={self.model_id}, name={self.name}, version={self.version})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_id': self.model_id,
            'name': self.name,
            'version': self.version,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'ratings': self.ratings,
            'stats': self.stats,
            'match_history': self.match_history
        }
