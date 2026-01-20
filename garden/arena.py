from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from datetime import datetime
import uuid


class Arena(ABC):
    def __init__(
        self,
        name: str,
        arena_id: Optional[str] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.arena_id = arena_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        
        self.match_history: List[str] = []
    
    @abstractmethod
    def evaluate(self, model_a: Any, model_b: Any, **kwargs) -> Dict[str, float]:
        pass
    
    def add_match(self, match_id: str):
        self.match_history.append(match_id)
    
    def __repr__(self) -> str:
        return f"Arena(id={self.arena_id}, name={self.name})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'arena_id': self.arena_id,
            'name': self.name,
            'description': self.description,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'total_matches': len(self.match_history)
        }


class BenchmarkArena(Arena):
    def __init__(
        self,
        name: str,
        benchmark_fn: Callable,
        arena_id: Optional[str] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        higher_is_better: bool = True
    ):
        super().__init__(name, arena_id, description, metadata)
        self.benchmark_fn = benchmark_fn
        self.higher_is_better = higher_is_better
    
    def evaluate(self, model_a: Any, model_b: Any, **kwargs) -> Dict[str, float]:
        score_a = self.benchmark_fn(model_a, **kwargs)
        score_b = self.benchmark_fn(model_b, **kwargs)
        
        return {
            'model_a_score': score_a,
            'model_b_score': score_b
        }
    
    def determine_winner(self, scores: Dict[str, float]) -> str:
        score_a = scores['model_a_score']
        score_b = scores['model_b_score']
        
        if self.higher_is_better:
            if score_a > score_b:
                return 'model_a'
            elif score_b > score_a:
                return 'model_b'
            else:
                return 'draw'
        else:
            if score_a < score_b:
                return 'model_a'
            elif score_b < score_a:
                return 'model_b'
            else:
                return 'draw'


class CustomArena(Arena):
    def __init__(
        self,
        name: str,
        evaluation_fn: Callable,
        arena_id: Optional[str] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name, arena_id, description, metadata)
        self.evaluation_fn = evaluation_fn
    
    def evaluate(self, model_a: Any, model_b: Any, **kwargs) -> Dict[str, float]:
        return self.evaluation_fn(model_a, model_b, **kwargs)
