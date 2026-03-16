"""
Bridge: MLflow ↔ Garden Integration

The single integration point between MLflow (training experiments) and
Garden (competitive arena evaluation). This module:

1. Registers trained models from MLflow runs into Garden for arena competition.
2. Optionally logs arena match results back to MLflow as a separate experiment.

Usage:
    from bridge import GardenBridge

    bridge = GardenBridge(garden, mlflow_tracking_uri='./mlruns')
    bridge.register_from_mlflow_run(run_id='abc123', model_name='my-transformer')
    bridge.enable_match_logging()  # optional: log arena results to MLflow too
"""

import mlflow
from typing import Optional, Dict, Any
from garden import Garden
from garden.match import Match


class GardenBridge:
    def __init__(
        self,
        garden: Garden,
        mlflow_tracking_uri: str = './mlruns',
        arena_experiment_name: str = 'arena_matches'
    ):
        self.garden = garden
        self.mlflow_tracking_uri = mlflow_tracking_uri
        self.arena_experiment_name = arena_experiment_name
        self._match_logging_enabled = False
    
    def register_from_mlflow_run(
        self,
        run_id: str,
        model_name: Optional[str] = None,
        version: str = "1.0",
        extra_metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a Garden model from a completed MLflow training run.
        
        Pulls hyperparameters and final metrics from the MLflow run and
        stores them as model metadata in Garden. This creates the link
        between a training experiment and an arena competitor.
        """
        mlflow.set_tracking_uri(self.mlflow_tracking_uri)
        run = mlflow.get_run(run_id)
        
        name = model_name or run.data.tags.get('mlflow.runName', f'model_{run_id[:8]}')
        
        metadata = {
            'mlflow_run_id': run_id,
            'mlflow_experiment_id': run.info.experiment_id,
            'training_params': dict(run.data.params),
            'training_metrics': {k: v for k, v in run.data.metrics.items()},
            'training_status': run.info.status,
        }
        if extra_metadata:
            metadata.update(extra_metadata)
        
        model = self.garden.register_model(
            name=name,
            version=version,
            metadata=metadata
        )
        
        return model
    
    def enable_match_logging(self):
        """Subscribe to Garden match events and log results to MLflow.
        
        This creates an 'arena_matches' experiment in MLflow so you can
        view match outcomes alongside training runs in the MLflow UI.
        """
        if self._match_logging_enabled:
            return
        
        self._match_logging_enabled = True
        self.garden.on_match_complete(self._log_match_to_mlflow)
    
    def _log_match_to_mlflow(self, match: Match):
        """Callback: log a completed match to MLflow."""
        if not match.result:
            return
        
        mlflow.set_tracking_uri(self.mlflow_tracking_uri)
        mlflow.set_experiment(self.arena_experiment_name)
        
        model_a = self.garden.models.get(match.model_a_id)
        model_b = self.garden.models.get(match.model_b_id)
        arena = self.garden.arenas.get(match.arena_id)
        
        with mlflow.start_run(run_name=f'match_{match.match_id[:8]}'):
            mlflow.log_params({
                'model_a_id': match.model_a_id,
                'model_b_id': match.model_b_id,
                'model_a_name': model_a.name if model_a else 'unknown',
                'model_b_name': model_b.name if model_b else 'unknown',
                'arena_id': match.arena_id,
                'arena_name': arena.name if arena else 'unknown',
            })
            
            mlflow.log_metrics({
                f'score_{match.model_a_id[:8]}': match.result.scores.get(match.model_a_id, 0),
                f'score_{match.model_b_id[:8]}': match.result.scores.get(match.model_b_id, 0),
            })
            
            for model_id, change in match.result.rating_changes.items():
                mlflow.log_metric(f'elo_change_{model_id[:8]}', change)
            
            mlflow.set_tag('winner', match.result.winner_id or 'draw')
            mlflow.set_tag('match_id', match.match_id)
    
    def get_mlflow_run_for_model(self, model_id: str) -> Optional[str]:
        """Get the MLflow run ID linked to a Garden model, if any."""
        model = self.garden.models.get(model_id)
        if model and model.metadata:
            return model.metadata.get('mlflow_run_id')
        return None
