from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import uuid
import itertools
import random


class TournamentType(Enum):
    ROUND_ROBIN = "round_robin"
    SINGLE_ELIMINATION = "single_elimination"
    DOUBLE_ELIMINATION = "double_elimination"
    SWISS = "swiss"


class TournamentStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Tournament:
    def __init__(
        self,
        name: str,
        arena_id: str,
        model_ids: List[str],
        tournament_type: TournamentType = TournamentType.ROUND_ROBIN,
        tournament_id: Optional[str] = None,
        season_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.tournament_id = tournament_id or str(uuid.uuid4())
        self.name = name
        self.arena_id = arena_id
        self.model_ids = model_ids
        self.tournament_type = tournament_type
        self.season_id = season_id
        self.metadata = metadata or {}
        
        self.status = TournamentStatus.SCHEDULED
        self.match_ids: List[str] = []
        self.standings: Dict[str, Dict[str, Any]] = {}
        
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        self._initialize_standings()
    
    def _initialize_standings(self):
        for model_id in self.model_ids:
            self.standings[model_id] = {
                'wins': 0,
                'losses': 0,
                'draws': 0,
                'points': 0,
                'matches_played': 0
            }
    
    def generate_matches(self) -> List[Tuple[str, str]]:
        if self.tournament_type == TournamentType.ROUND_ROBIN:
            return self._generate_round_robin()
        elif self.tournament_type == TournamentType.SINGLE_ELIMINATION:
            return self._generate_single_elimination()
        elif self.tournament_type == TournamentType.SWISS:
            return self._generate_swiss_round()
        else:
            raise NotImplementedError(f"Tournament type {self.tournament_type} not implemented")
    
    def _generate_round_robin(self) -> List[Tuple[str, str]]:
        return list(itertools.combinations(self.model_ids, 2))
    
    def _generate_single_elimination(self) -> List[Tuple[str, str]]:
        models = self.model_ids.copy()
        random.shuffle(models)
        
        while len(models) < self._next_power_of_2(len(models)):
            models.append(None)
        
        matches = []
        for i in range(0, len(models), 2):
            if models[i] is not None and models[i + 1] is not None:
                matches.append((models[i], models[i + 1]))
        
        return matches
    
    def _generate_swiss_round(self, round_num: int = 1) -> List[Tuple[str, str]]:
        sorted_models = sorted(
            self.model_ids,
            key=lambda m: self.standings[m]['points'],
            reverse=True
        )
        
        matches = []
        paired = set()
        
        for i, model_a in enumerate(sorted_models):
            if model_a in paired:
                continue
            
            for model_b in sorted_models[i + 1:]:
                if model_b not in paired:
                    matches.append((model_a, model_b))
                    paired.add(model_a)
                    paired.add(model_b)
                    break
        
        return matches
    
    def _next_power_of_2(self, n: int) -> int:
        power = 1
        while power < n:
            power *= 2
        return power
    
    def start(self):
        self.status = TournamentStatus.IN_PROGRESS
        self.started_at = datetime.now()
    
    def complete(self):
        self.status = TournamentStatus.COMPLETED
        self.completed_at = datetime.now()
    
    def cancel(self):
        self.status = TournamentStatus.CANCELLED
        self.completed_at = datetime.now()
    
    def add_match(self, match_id: str):
        self.match_ids.append(match_id)
    
    def update_standings(self, model_id: str, result: str, points: float = 0):
        if model_id not in self.standings:
            return
        
        self.standings[model_id]['matches_played'] += 1
        
        if result == 'win':
            self.standings[model_id]['wins'] += 1
            self.standings[model_id]['points'] += 3
        elif result == 'loss':
            self.standings[model_id]['losses'] += 1
        elif result == 'draw':
            self.standings[model_id]['draws'] += 1
            self.standings[model_id]['points'] += 1
        
        self.standings[model_id]['points'] += points
    
    def get_rankings(self) -> List[Tuple[str, Dict[str, Any]]]:
        return sorted(
            self.standings.items(),
            key=lambda x: (x[1]['points'], x[1]['wins']),
            reverse=True
        )
    
    def __repr__(self) -> str:
        return f"Tournament(id={self.tournament_id}, name={self.name}, type={self.tournament_type.value}, status={self.status.value})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tournament_id': self.tournament_id,
            'name': self.name,
            'arena_id': self.arena_id,
            'model_ids': self.model_ids,
            'tournament_type': self.tournament_type.value,
            'season_id': self.season_id,
            'status': self.status.value,
            'match_ids': self.match_ids,
            'standings': self.standings,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata': self.metadata
        }
