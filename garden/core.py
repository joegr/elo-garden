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
from . import tracking
from .metrics import MetricsLogger, EvaluationMetric
import mlflow


class Garden:
    def __init__(
        self,
        name: str = "Garden",
        elo_k_factor: int = 32,
        initial_rating: float = 1500,
        data_dir: str = "garden_data",
        tracking_uri: Optional[str] = None,
        enable_mlflow_tracking: bool = True
    ):
        self.name = name
        self.elo_system = ELOSystem(k_factor=elo_k_factor, initial_rating=initial_rating)
        self.data_dir = data_dir
        self.enable_mlflow_tracking = enable_mlflow_tracking
        
        self.models: Dict[str, Model] = {}
        self.arenas: Dict[str, Arena] = {}
        self.matches: Dict[str, Match] = {}
        self.tournaments: Dict[str, Tournament] = {}
        self.seasons: Dict[str, Season] = {}
        self.leaderboards: Dict[str, Leaderboard] = {}
        
        self.created_at = datetime.now()
        
        os.makedirs(data_dir, exist_ok=True)
        
        if self.enable_mlflow_tracking:
            tracking_path = tracking_uri or os.path.join(data_dir, "mlruns")
            mlflow.set_tracking_uri(tracking_path)
            self.tracking_uri = tracking_path
            self.metrics_logger = MetricsLogger()
        else:
            self.tracking_uri = None
            self.metrics_logger = None
    
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
        
        if self.enable_mlflow_tracking:
            experiment_name = f"arena_{self.arenas[arena_id].name}"
            if tournament_id:
                experiment_name = f"tournament_{self.tournaments[tournament_id].name}"
            mlflow.set_experiment(experiment_name)
            mlflow.start_run(run_name=f"match_{match.match_id[:8]}")
        
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
        
        if self.enable_mlflow_tracking:
            mlflow.log_params({
                'model_a_id': model_a_id,
                'model_b_id': model_b_id,
                'arena_id': arena_id,
                'arena_name': arena.name,
                'model_a_name': model_a.name,
                'model_b_name': model_b.name,
                'tournament_id': tournament_id or '',
                'season_id': season_id or ''
            })
            
            mlflow.log_metrics({
                'model_a_score': scores['model_a_score'],
                'model_b_score': scores['model_b_score'],
                'model_a_rating_before': rating_a,
                'model_b_rating_before': rating_b,
                'model_a_rating_after': new_rating_a,
                'model_b_rating_after': new_rating_b,
                'model_a_rating_change': new_rating_a - rating_a,
                'model_b_rating_change': new_rating_b - rating_b
            })
            
            mlflow.set_tags({
                'winner': winner_id or 'draw',
                'match_type': 'tournament' if tournament_id else 'standalone',
                'arena_type': arena.__class__.__name__
            })
            
            mlflow.end_run()
        
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
        version: str,
        arena_id: Optional[str] = None,
        season_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ontology: Optional[Dict[str, Any]] = None
    ) -> Model:
        model = Model(
            name=name,
            model_id=model_id,
            version=version,
            metadata=metadata,
            ontology=ontology
        )
        self.models[model_id] = model
        
        if arena_id and arena_id in self.arenas:
            self.arenas[arena_id].add_model(model_id)
        
        if season_id and season_id in self.seasons:
            self.seasons[season_id].add_model(model_id)
    
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
    
    def register_metric(self, metric: EvaluationMetric):
        if self.metrics_logger:
            self.metrics_logger.register_metric(metric)
    
    def evaluate_with_metric(
        self,
        metric_name: str,
        model_id: str,
        data: Any,
        **kwargs
    ) -> Optional[Any]:
        if not self.metrics_logger:
            return None
        
        import pandas as pd
        if not isinstance(data, pd.Series):
            data = pd.Series(data)
        
        return self.metrics_logger.evaluate(metric_name, data, **kwargs)
    
    def get_tracking_uri(self) -> Optional[str]:
        return self.tracking_uri
    
    def get_metrics_logger(self) -> Optional[MetricsLogger]:
        return self.metrics_logger
    
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
