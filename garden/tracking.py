"""Garden tracking module - wrapper around real MLflow"""

import mlflow
from mlflow.entities import Experiment, Run
from typing import Dict, List, Optional, Any
from contextlib import contextmanager


def set_tracking_uri(uri: str):
    """Set the MLflow tracking URI"""
    mlflow.set_tracking_uri(uri)


def get_tracking_uri() -> str:
    """Get the MLflow tracking URI"""
    return mlflow.get_tracking_uri()


def create_experiment(
    name: str,
    artifact_location: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None
) -> str:
    """Create a new MLflow experiment"""
    return mlflow.create_experiment(name, artifact_location=artifact_location, tags=tags)


def set_experiment(experiment_name: str):
    """Set the active MLflow experiment"""
    return mlflow.set_experiment(experiment_name)


def get_experiment(experiment_id: str) -> Optional[Experiment]:
    """Get an MLflow experiment by ID"""
    return mlflow.get_experiment(experiment_id)


def get_experiment_by_name(name: str) -> Optional[Experiment]:
    """Get an MLflow experiment by name"""
    return mlflow.get_experiment_by_name(name)


def start_run(
    run_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    run_name: Optional[str] = None,
    nested: bool = False,
    tags: Optional[Dict[str, str]] = None,
    description: Optional[str] = None
) -> mlflow.ActiveRun:
    """Start a new MLflow run"""
    return mlflow.start_run(
        run_id=run_id,
        experiment_id=experiment_id,
        run_name=run_name,
        nested=nested,
        tags=tags,
        description=description
    )


def end_run(status: str = "FINISHED"):
    """End the active MLflow run"""
    mlflow.end_run(status=status)


def active_run() -> Optional[mlflow.ActiveRun]:
    """Get the active MLflow run"""
    return mlflow.active_run()


def last_active_run() -> Optional[Run]:
    """Get the last active MLflow run"""
    return mlflow.last_active_run()


def log_param(key: str, value: Any):
    """Log a parameter to MLflow"""
    mlflow.log_param(key, value)


def log_params(params: Dict[str, Any]):
    """Log multiple parameters to MLflow"""
    mlflow.log_params(params)


def log_metric(key: str, value: float, step: Optional[int] = None):
    """Log a metric to MLflow"""
    mlflow.log_metric(key, value, step=step)


def log_metrics(metrics: Dict[str, float], step: Optional[int] = None):
    """Log multiple metrics to MLflow"""
    mlflow.log_metrics(metrics, step=step)


def set_tag(key: str, value: str):
    """Set a tag in MLflow"""
    mlflow.set_tag(key, value)


def set_tags(tags: Dict[str, str]):
    """Set multiple tags in MLflow"""
    mlflow.set_tags(tags)


def log_artifact(local_path: str, artifact_path: Optional[str] = None):
    """Log an artifact to MLflow"""
    mlflow.log_artifact(local_path, artifact_path=artifact_path)


def log_artifacts(local_dir: str, artifact_path: Optional[str] = None):
    """Log a directory of artifacts to MLflow"""
    mlflow.log_artifacts(local_dir, artifact_path=artifact_path)


def get_artifact_uri() -> Optional[str]:
    """Get the artifact URI for the active run"""
    return mlflow.get_artifact_uri()


def search_runs(
    experiment_ids: Optional[List[str]] = None,
    filter_string: str = "",
    max_results: int = 1000,
    order_by: Optional[List[str]] = None
) -> List[Run]:
    """Search MLflow runs"""
    return mlflow.search_runs(
        experiment_ids=experiment_ids,
        filter_string=filter_string,
        max_results=max_results,
        order_by=order_by,
        output_format="list"
    )


def get_run(run_id: str) -> Run:
    """Get an MLflow run by ID"""
    return mlflow.get_run(run_id)


@contextmanager
def run_context(run_name: Optional[str] = None, **kwargs):
    """Context manager for MLflow runs"""
    with mlflow.start_run(run_name=run_name, **kwargs) as run:
        yield run
