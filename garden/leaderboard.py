from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid


class Leaderboard:
    def __init__(
        self,
        name: str,
        arena_id: Optional[str] = None,
        season_id: Optional[str] = None,
        leaderboard_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.leaderboard_id = leaderboard_id or str(uuid.uuid4())
        self.name = name
        self.arena_id = arena_id
        self.season_id = season_id
        self.metadata = metadata or {}
        
        self.rankings: List[Dict[str, Any]] = []
        self.last_updated = datetime.now()
        self.created_at = datetime.now()
    
    def update(self, model_ratings: Dict[str, float], model_stats: Dict[str, Dict[str, Any]]):
        self.rankings = []
        
        for model_id, rating in model_ratings.items():
            stats = model_stats.get(model_id, {})
            
            entry = {
                'model_id': model_id,
                'rating': rating,
                'rank': 0,
                'total_matches': stats.get('total_matches', 0),
                'wins': stats.get('wins', 0),
                'losses': stats.get('losses', 0),
                'draws': stats.get('draws', 0),
                'win_rate': stats.get('win_rate', 0.0)
            }
            
            self.rankings.append(entry)
        
        self.rankings.sort(key=lambda x: x['rating'], reverse=True)
        
        for rank, entry in enumerate(self.rankings, start=1):
            entry['rank'] = rank
        
        self.last_updated = datetime.now()
    
    def get_top_n(self, n: int = 10) -> List[Dict[str, Any]]:
        return self.rankings[:n]
    
    def get_model_rank(self, model_id: str) -> Optional[int]:
        for entry in self.rankings:
            if entry['model_id'] == model_id:
                return entry['rank']
        return None
    
    def get_model_entry(self, model_id: str) -> Optional[Dict[str, Any]]:
        for entry in self.rankings:
            if entry['model_id'] == model_id:
                return entry
        return None
    
    def get_percentile(self, model_id: str) -> Optional[float]:
        rank = self.get_model_rank(model_id)
        if rank is None or len(self.rankings) == 0:
            return None
        
        return (1 - (rank - 1) / len(self.rankings)) * 100
    
    def format_table(self, top_n: int = 10) -> str:
        lines = []
        lines.append(f"\n{'='*80}")
        lines.append(f"{self.name} - Leaderboard")
        lines.append(f"{'='*80}")
        lines.append(f"{'Rank':<6} {'Model ID':<20} {'Rating':<10} {'W/L/D':<15} {'Win Rate':<10}")
        lines.append(f"{'-'*80}")
        
        for entry in self.get_top_n(top_n):
            wld = f"{entry['wins']}/{entry['losses']}/{entry['draws']}"
            win_rate = f"{entry['win_rate']*100:.1f}%"
            
            lines.append(
                f"{entry['rank']:<6} "
                f"{entry['model_id'][:20]:<20} "
                f"{entry['rating']:<10.1f} "
                f"{wld:<15} "
                f"{win_rate:<10}"
            )
        
        lines.append(f"{'='*80}\n")
        
        return '\n'.join(lines)
    
    def __repr__(self) -> str:
        return f"Leaderboard(id={self.leaderboard_id}, name={self.name}, entries={len(self.rankings)})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'leaderboard_id': self.leaderboard_id,
            'name': self.name,
            'arena_id': self.arena_id,
            'season_id': self.season_id,
            'rankings': self.rankings,
            'last_updated': self.last_updated.isoformat(),
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }
