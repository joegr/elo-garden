from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json
import os

from .model import Model
from .arena import Arena, BenchmarkArena
from .match import Match, MatchResult, MatchStatus
from .tournament import Tournament, TournamentType, TournamentStatus
from .season import Season, SeasonStatus
from .leaderboard import Leaderboard
from .elo import ELOSystem
from .db import GardenDB


class Garden:
    def __init__(
        self,
        name: str = "Garden",
        elo_k_factor: int = 32,
        initial_rating: float = 1500,
        data_dir: str = "garden_data",
        db_path: Optional[str] = None
    ):
        self.name = name
        self.elo_system = ELOSystem(k_factor=elo_k_factor, initial_rating=initial_rating)
        self.data_dir = data_dir
        
        self.models: Dict[str, Model] = {}
        self.arenas: Dict[str, Arena] = {}
        self.matches: Dict[str, Match] = {}
        self.tournaments: Dict[str, Tournament] = {}
        self.seasons: Dict[str, Season] = {}
        self.leaderboards: Dict[str, Leaderboard] = {}
        
        # Event listeners — external systems (e.g. bridge.py) can subscribe
        self._on_match_complete: List[Callable[[Match], None]] = []
        self._on_model_registered: List[Callable[[Model], None]] = []
        
        self.created_at = datetime.now()
        
        os.makedirs(data_dir, exist_ok=True)
        
        # SQLite persistence — if db_path provided, auto-persist all mutations
        self.db: Optional[GardenDB] = None
        if db_path is not None:
            self.db = GardenDB(db_path)
            self._load_from_db()
    
    def _persist_model(self, model: Model):
        """Persist a model to the DB if DB is enabled."""
        if self.db:
            self.db.save_model(
                model_id=model.model_id,
                name=model.name,
                version=model.version,
                metadata=model.metadata,
                ratings=model.ratings,
                stats=model.stats,
                ontology=model.ontology.to_dict() if model.ontology else None,
                match_history=model.match_history,
                created_at=model.created_at.isoformat() if hasattr(model, 'created_at') and model.created_at else datetime.now().isoformat()
            )
    
    def _persist_match(self, match: Match):
        """Persist a match to the DB if DB is enabled."""
        if self.db:
            self.db.save_match(
                match_id=match.match_id,
                model_a_id=match.model_a_id,
                model_b_id=match.model_b_id,
                arena_id=match.arena_id,
                status=match.status.value if hasattr(match.status, 'value') else str(match.status),
                winner_id=match.result.winner_id if match.result else None,
                scores=match.result.scores if match.result else {},
                rating_changes=match.result.rating_changes if match.result else {},
                tournament_id=match.tournament_id if hasattr(match, 'tournament_id') else None,
                season_id=match.season_id if hasattr(match, 'season_id') else None,
                started_at=match.started_at.isoformat() if hasattr(match, 'started_at') and match.started_at else None,
                completed_at=match.completed_at.isoformat() if hasattr(match, 'completed_at') and match.completed_at else None,
                created_at=match.created_at.isoformat() if hasattr(match, 'created_at') and match.created_at else datetime.now().isoformat()
            )
    
    def _persist_arena(self, arena: Arena):
        """Persist an arena to the DB if DB is enabled."""
        if self.db:
            self.db.save_arena(
                arena_id=arena.arena_id,
                name=arena.name,
                description=arena.description,
                arena_type=arena.__class__.__name__,
                higher_is_better=getattr(arena, 'higher_is_better', True),
                metadata=getattr(arena, 'metadata', {}) or {},
                match_history=arena.match_history,
                created_at=datetime.now().isoformat()
            )
    
    def _load_from_db(self):
        """Restore in-memory state from SQLite on startup."""
        if not self.db:
            return
        
        # Load models
        for row in self.db.load_models():
            from .ontology import ModelOntology
            ontology = None
            if row['ontology']:
                try:
                    ontology = ModelOntology.from_dict(row['ontology'])
                except Exception:
                    pass
            model = Model(
                name=row['name'],
                model_id=row['model_id'],
                version=row['version'],
                metadata=row['metadata'],
                ontology=ontology
            )
            model.ratings = row['ratings']
            model.stats = row['stats']
            model.match_history = row['match_history']
            self.models[model.model_id] = model
        
        # Load matches (metadata only — the Match objects are lightweight)
        for row in self.db.load_matches():
            match = Match(
                model_a_id=row['model_a_id'],
                model_b_id=row['model_b_id'],
                arena_id=row['arena_id'],
                match_id=row['match_id']
            )
            match.status = MatchStatus(row['status']) if row['status'] in [s.value for s in MatchStatus] else MatchStatus.COMPLETED
            if row['winner_id'] or row['scores']:
                match.result = MatchResult(
                    match_id=row['match_id'],
                    winner_id=row['winner_id'],
                    scores=row['scores'],
                    rating_changes=row['rating_changes']
                )
            self.matches[match.match_id] = match
    
    def on_match_complete(self, callback: Callable[[Match], None]):
        """Register a callback that fires after every match completion."""
        self._on_match_complete.append(callback)
    
    def on_model_registered(self, callback: Callable[[Model], None]):
        """Register a callback that fires after a model is registered."""
        self._on_model_registered.append(callback)
    
    def register_model(
        self,
        name: str,
        model_id: Optional[str] = None,
        version: str = "1.0",
        metadata: Optional[Dict[str, Any]] = None,
        ontology: Optional[Any] = None
    ) -> Model:
        model = Model(name, model_id, version, metadata, ontology)
        self.models[model.model_id] = model
        self._persist_model(model)
        for cb in self._on_model_registered:
            cb(model)
        return model
    
    def register_arena(self, arena: Arena) -> Arena:
        self.arenas[arena.arena_id] = arena
        return arena
    
    def create_benchmark_arena(
        self,
        name: str,
        benchmark_fn: Callable,
        description: str = "",
        higher_is_better: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> BenchmarkArena:
        arena = BenchmarkArena(
            name=name,
            benchmark_fn=benchmark_fn,
            description=description,
            metadata=metadata,
            higher_is_better=higher_is_better
        )
        self.arenas[arena.arena_id] = arena
        self._persist_arena(arena)
        return arena
    
    def create_season(
        self,
        name: str,
        arena_ids: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Season:
        season = Season(name, arena_ids, start_date=start_date, end_date=end_date, metadata=metadata)
        self.seasons[season.season_id] = season
        return season
    
    def create_tournament(
        self,
        name: str,
        arena_id: str,
        model_ids: List[str],
        tournament_type: TournamentType = TournamentType.ROUND_ROBIN,
        season_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tournament:
        tournament = Tournament(
            name=name,
            arena_id=arena_id,
            model_ids=model_ids,
            tournament_type=tournament_type,
            season_id=season_id,
            metadata=metadata
        )
        self.tournaments[tournament.tournament_id] = tournament
        
        if season_id and season_id in self.seasons:
            self.seasons[season_id].add_tournament(tournament.tournament_id)
        
        return tournament
    
    def run_match(
        self,
        model_a_id: str,
        model_b_id: str,
        arena_id: str,
        tournament_id: Optional[str] = None,
        season_id: Optional[str] = None,
        **kwargs
    ) -> Match:
        if model_a_id not in self.models:
            raise ValueError(f"Model {model_a_id} not found")
        if model_b_id not in self.models:
            raise ValueError(f"Model {model_b_id} not found")
        if arena_id not in self.arenas:
            raise ValueError(f"Arena {arena_id} not found")
        
        match = Match(
            model_a_id=model_a_id,
            model_b_id=model_b_id,
            arena_id=arena_id,
            tournament_id=tournament_id,
            season_id=season_id
        )
        
        self.matches[match.match_id] = match
        match.start()
        
        model_a = self.models[model_a_id]
        model_b = self.models[model_b_id]
        arena = self.arenas[arena_id]
        
        scores = arena.evaluate(model_a, model_b, **kwargs)
        
        rating_a = model_a.get_rating(arena_id, self.elo_system.initial_rating)
        rating_b = model_b.get_rating(arena_id, self.elo_system.initial_rating)
        
        if isinstance(arena, BenchmarkArena):
            winner = arena.determine_winner(scores)
            
            if winner == 'model_a':
                score_a, score_b = 1.0, 0.0
                winner_id = model_a_id
                model_a.update_stats('win')
                model_b.update_stats('loss')
            elif winner == 'model_b':
                score_a, score_b = 0.0, 1.0
                winner_id = model_b_id
                model_a.update_stats('loss')
                model_b.update_stats('win')
            else:
                score_a, score_b = 0.5, 0.5
                winner_id = None
                model_a.update_stats('draw')
                model_b.update_stats('draw')
        else:
            score_a = scores.get('model_a_score', 0.5)
            score_b = scores.get('model_b_score', 0.5)
            
            if score_a > score_b:
                winner_id = model_a_id
                model_a.update_stats('win')
                model_b.update_stats('loss')
            elif score_b > score_a:
                winner_id = model_b_id
                model_a.update_stats('loss')
                model_b.update_stats('win')
            else:
                winner_id = None
                model_a.update_stats('draw')
                model_b.update_stats('draw')
        
        new_rating_a, new_rating_b = self.elo_system.update_ratings(
            rating_a, rating_b, score_a, score_b
        )
        
        model_a.set_rating(arena_id, new_rating_a)
        model_b.set_rating(arena_id, new_rating_b)
        model_a.add_match(match.match_id)
        model_b.add_match(match.match_id)
        
        result = MatchResult(
            match_id=match.match_id,
            winner_id=winner_id,
            scores={model_a_id: scores['model_a_score'], model_b_id: scores['model_b_score']},
            rating_changes={
                model_a_id: new_rating_a - rating_a,
                model_b_id: new_rating_b - rating_b
            }
        )
        
        match.complete(result)
        
        arena.add_match(match.match_id)
        
        if tournament_id and tournament_id in self.tournaments:
            tournament = self.tournaments[tournament_id]
            tournament.add_match(match.match_id)
            
            if winner_id == model_a_id:
                tournament.update_standings(model_a_id, 'win')
                tournament.update_standings(model_b_id, 'loss')
            elif winner_id == model_b_id:
                tournament.update_standings(model_b_id, 'win')
                tournament.update_standings(model_a_id, 'loss')
            else:
                tournament.update_standings(model_a_id, 'draw')
                tournament.update_standings(model_b_id, 'draw')
        
        if season_id and season_id in self.seasons:
            season = self.seasons[season_id]
            season.add_match(match.match_id)
            season.update_rating(arena_id, model_a_id, new_rating_a)
            season.update_rating(arena_id, model_b_id, new_rating_b)
        
        # Persist match result and updated model ratings
        self._persist_match(match)
        self._persist_model(model_a)
        self._persist_model(model_b)
        
        # Fire event callbacks
        for cb in self._on_match_complete:
            cb(match)
        
        return match
    
    def run_tournament(self, tournament_id: str, **kwargs) -> Tournament:
        if tournament_id not in self.tournaments:
            raise ValueError(f"Tournament {tournament_id} not found")
        
        tournament = self.tournaments[tournament_id]
        tournament.start()
        
        matchups = tournament.generate_matches()
        
        for model_a_id, model_b_id in matchups:
            self.run_match(
                model_a_id=model_a_id,
                model_b_id=model_b_id,
                arena_id=tournament.arena_id,
                tournament_id=tournament_id,
                season_id=tournament.season_id,
                **kwargs
            )
        
        tournament.complete()
        return tournament
    
    def create_leaderboard(
        self,
        name: str,
        arena_id: Optional[str] = None,
        season_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Leaderboard:
        leaderboard = Leaderboard(
            name=name,
            arena_id=arena_id,
            season_id=season_id,
            metadata=metadata
        )
        self.leaderboards[leaderboard.leaderboard_id] = leaderboard
        return leaderboard
    
    def update_leaderboard(self, leaderboard_id: str):
        if leaderboard_id not in self.leaderboards:
            raise ValueError(f"Leaderboard {leaderboard_id} not found")
        
        leaderboard = self.leaderboards[leaderboard_id]
        
        model_ratings = {}
        model_stats = {}
        
        for model_id, model in self.models.items():
            if leaderboard.arena_id:
                rating = model.get_rating(leaderboard.arena_id, self.elo_system.initial_rating)
            else:
                ratings = list(model.ratings.values())
                rating = sum(ratings) / len(ratings) if ratings else self.elo_system.initial_rating
            
            model_ratings[model_id] = rating
            model_stats[model_id] = model.stats
        
        leaderboard.update(model_ratings, model_stats)
    
    def get_leaderboard(self, leaderboard_id: str) -> Leaderboard:
        if leaderboard_id not in self.leaderboards:
            raise ValueError(f"Leaderboard {leaderboard_id} not found")
        
        self.update_leaderboard(leaderboard_id)
        return self.leaderboards[leaderboard_id]
    
    def save_state(self, filename: Optional[str] = None):
        if filename is None:
            filename = f"garden_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.data_dir, filename)
        
        state = {
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'models': {k: v.to_dict() for k, v in self.models.items()},
            'arenas': {k: v.to_dict() for k, v in self.arenas.items()},
            'matches': {k: v.to_dict() for k, v in self.matches.items()},
            'tournaments': {k: v.to_dict() for k, v in self.tournaments.items()},
            'seasons': {k: v.to_dict() for k, v in self.seasons.items()},
            'leaderboards': {k: v.to_dict() for k, v in self.leaderboards.items()}
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"Garden state saved to {filepath}")
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            'total_models': len(self.models),
            'total_arenas': len(self.arenas),
            'total_matches': len(self.matches),
            'total_tournaments': len(self.tournaments),
            'total_seasons': len(self.seasons),
            'completed_matches': sum(1 for m in self.matches.values() if m.status == MatchStatus.COMPLETED),
            'active_tournaments': sum(1 for t in self.tournaments.values() if t.status == TournamentStatus.IN_PROGRESS),
            'active_seasons': sum(1 for s in self.seasons.values() if s.status == SeasonStatus.ACTIVE)
        }
    
    def get_models_by_elo_range(
        self,
        arena_id: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None
    ) -> List[Model]:
        """Get models within a specific ELO rating range"""
        results = []
        
        for model in self.models.values():
            if arena_id:
                rating = model.get_rating(arena_id, self.elo_system.initial_rating)
            else:
                ratings = list(model.ratings.values())
                rating = sum(ratings) / len(ratings) if ratings else self.elo_system.initial_rating
            
            if min_rating is not None and rating < min_rating:
                continue
            if max_rating is not None and rating > max_rating:
                continue
            
            results.append(model)
        
        if arena_id:
            results.sort(key=lambda m: m.get_rating(arena_id, self.elo_system.initial_rating), reverse=True)
        else:
            results.sort(key=lambda m: (sum(m.ratings.values()) / len(m.ratings.values()) if m.ratings.values() else self.elo_system.initial_rating), reverse=True)
        
        return results
    
    def find_best_matchup(
        self,
        model_id: str,
        arena_id: Optional[str] = None,
        rating_tolerance: float = 200,
        min_matches: int = 0
    ) -> Optional[Model]:
        """Find the best opponent for a given model based on ELO proximity"""
        if model_id not in self.models:
            return None
        
        target_model = self.models[model_id]
        target_rating = target_model.get_rating(
            arena_id if arena_id else list(target_model.ratings.keys())[0] if target_model.ratings else None,
            self.elo_system.initial_rating
        )
        
        candidates = []
        for candidate in self.models.values():
            if candidate.model_id == model_id:
                continue
            
            if candidate.stats['total_matches'] < min_matches:
                continue
            
            cand_rating = candidate.get_rating(
                arena_id if arena_id else list(candidate.ratings.keys())[0] if candidate.ratings else None,
                self.elo_system.initial_rating
            )
            
            rating_diff = abs(target_rating - cand_rating)
            if rating_diff <= rating_tolerance:
                candidates.append((candidate, rating_diff))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]
    
    def get_elo_leaderboard(
        self,
        arena_id: Optional[str] = None,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top models by ELO rating"""
        model_ratings = []
        
        for model in self.models.values():
            if arena_id:
                rating = model.get_rating(arena_id, self.elo_system.initial_rating)
            else:
                ratings = list(model.ratings.values())
                rating = sum(ratings) / len(ratings) if ratings else self.elo_system.initial_rating
            
            model_ratings.append({
                'model_id': model.model_id,
                'name': model.name,
                'version': model.version,
                'rating': rating,
                'total_matches': model.stats['total_matches'],
                'win_rate': model.stats['win_rate']
            })
        
        model_ratings.sort(key=lambda x: x['rating'], reverse=True)
        return model_ratings[:top_n]
    
    def __repr__(self) -> str:
        stats = self.get_stats()
        return f"Garden(name={self.name}, models={stats['total_models']}, arenas={stats['total_arenas']}, matches={stats['total_matches']})"
