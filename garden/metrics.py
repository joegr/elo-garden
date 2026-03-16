from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np


@dataclass
class MetricValue:
    scores: Optional[List[float]] = None
    justifications: Optional[List[str]] = None
    aggregate_results: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        if self.scores is None:
            self.scores = []
        if self.justifications is None:
            self.justifications = []
        if self.aggregate_results is None:
            self.aggregate_results = {}


class EvaluationMetric(ABC):
    def __init__(
        self,
        name: str,
        greater_is_better: bool = True,
        long_name: Optional[str] = None,
        version: Optional[str] = None,
        metric_details: Optional[str] = None,
        metric_metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.greater_is_better = greater_is_better
        self.long_name = long_name or name
        self.version = version or "v1"
        self.metric_details = metric_details or f"Computes {name} metric"
        self.metric_metadata = metric_metadata or {}
    
    @abstractmethod
    def eval_fn(
        self,
        predictions: pd.Series,
        targets: Optional[pd.Series] = None,
        metrics: Optional[Dict[str, MetricValue]] = None,
        **kwargs
    ) -> Union[float, MetricValue]:
        pass
    
    def compute(
        self,
        predictions: pd.Series,
        targets: Optional[pd.Series] = None,
        **kwargs
    ) -> MetricValue:
        result = self.eval_fn(predictions, targets, **kwargs)
        
        if isinstance(result, MetricValue):
            return result
        elif isinstance(result, (int, float)):
            return MetricValue(aggregate_results={'score': float(result)})
        else:
            return MetricValue(aggregate_results={'score': 0.0})


class ELORatingMetric(EvaluationMetric):
    def __init__(self, k_factor: int = 32, initial_rating: float = 1500):
        super().__init__(
            name="elo_rating",
            greater_is_better=True,
            long_name="ELO Rating",
            metric_details="Computes ELO rating changes based on match outcomes"
        )
        self.k_factor = k_factor
        self.initial_rating = initial_rating
    
    def eval_fn(
        self,
        predictions: pd.Series,
        targets: Optional[pd.Series] = None,
        metrics: Optional[Dict[str, MetricValue]] = None,
        **kwargs
    ) -> MetricValue:
        import math
        
        ratings = kwargs.get('ratings', {})
        outcomes = kwargs.get('outcomes', {})
        
        rating_changes = []
        for idx, pred in predictions.items():
            if idx in ratings and idx in outcomes:
                rating_a = ratings[idx].get('model_a', self.initial_rating)
                rating_b = ratings[idx].get('model_b', self.initial_rating)
                outcome = outcomes[idx]
                
                expected_a = 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))
                expected_b = 1 / (1 + math.pow(10, (rating_a - rating_b) / 400))
                
                if outcome == 'model_a':
                    score_a, score_b = 1.0, 0.0
                elif outcome == 'model_b':
                    score_a, score_b = 0.0, 1.0
                else:
                    score_a, score_b = 0.5, 0.5
                
                change_a = self.k_factor * (score_a - expected_a)
                change_b = self.k_factor * (score_b - expected_b)
                
                rating_changes.append({
                    'model_a_change': change_a,
                    'model_b_change': change_b
                })
        
        avg_change = np.mean([abs(rc['model_a_change']) for rc in rating_changes]) if rating_changes else 0.0
        
        return MetricValue(
            scores=[rc['model_a_change'] for rc in rating_changes],
            aggregate_results={
                'mean_rating_change': avg_change,
                'total_matches': len(rating_changes)
            }
        )


class WinRateMetric(EvaluationMetric):
    def __init__(self):
        super().__init__(
            name="win_rate",
            greater_is_better=True,
            long_name="Win Rate",
            metric_details="Computes win rate as wins / total_matches"
        )
    
    def eval_fn(
        self,
        predictions: pd.Series,
        targets: Optional[pd.Series] = None,
        metrics: Optional[Dict[str, MetricValue]] = None,
        **kwargs
    ) -> MetricValue:
        wins = kwargs.get('wins', 0)
        total_matches = kwargs.get('total_matches', 0)
        
        win_rate = wins / total_matches if total_matches > 0 else 0.0
        
        return MetricValue(
            aggregate_results={
                'win_rate': win_rate,
                'wins': wins,
                'total_matches': total_matches
            }
        )


class AccuracyMetric(EvaluationMetric):
    def __init__(self):
        super().__init__(
            name="accuracy",
            greater_is_better=True,
            long_name="Accuracy Score",
            metric_details="Computes accuracy as correct predictions / total predictions"
        )
    
    def eval_fn(
        self,
        predictions: pd.Series,
        targets: Optional[pd.Series] = None,
        metrics: Optional[Dict[str, MetricValue]] = None,
        **kwargs
    ) -> MetricValue:
        if targets is None:
            return MetricValue(aggregate_results={'accuracy': 0.0})
        
        correct = (predictions == targets).sum()
        total = len(predictions)
        accuracy = correct / total if total > 0 else 0.0
        
        per_row_scores = (predictions == targets).astype(float).tolist()
        
        return MetricValue(
            scores=per_row_scores,
            aggregate_results={
                'accuracy': accuracy,
                'correct': int(correct),
                'total': total
            }
        )


class LatencyMetric(EvaluationMetric):
    def __init__(self):
        super().__init__(
            name="latency",
            greater_is_better=False,
            long_name="Inference Latency",
            metric_details="Measures inference latency in milliseconds"
        )
    
    def eval_fn(
        self,
        predictions: pd.Series,
        targets: Optional[pd.Series] = None,
        metrics: Optional[Dict[str, MetricValue]] = None,
        **kwargs
    ) -> MetricValue:
        latencies = kwargs.get('latencies', [])
        
        if not latencies:
            return MetricValue(aggregate_results={'mean_latency': 0.0})
        
        mean_latency = np.mean(latencies)
        median_latency = np.median(latencies)
        p95_latency = np.percentile(latencies, 95)
        p99_latency = np.percentile(latencies, 99)
        
        return MetricValue(
            scores=latencies,
            aggregate_results={
                'mean_latency_ms': mean_latency,
                'median_latency_ms': median_latency,
                'p95_latency_ms': p95_latency,
                'p99_latency_ms': p99_latency,
                'min_latency_ms': min(latencies),
                'max_latency_ms': max(latencies)
            }
        )


class PerplexityMetric(EvaluationMetric):
    def __init__(self):
        super().__init__(
            name="perplexity",
            greater_is_better=False,
            long_name="Perplexity",
            metric_details="Computes perplexity metric for language models"
        )
    
    def eval_fn(
        self,
        predictions: pd.Series,
        targets: Optional[pd.Series] = None,
        metrics: Optional[Dict[str, MetricValue]] = None,
        **kwargs
    ) -> MetricValue:
        import math
        
        log_likelihoods = kwargs.get('log_likelihoods', [])
        
        if not log_likelihoods:
            return MetricValue(aggregate_results={'perplexity': float('inf')})
        
        avg_log_likelihood = np.mean(log_likelihoods)
        perplexity = math.exp(-avg_log_likelihood)
        
        return MetricValue(
            scores=log_likelihoods,
            aggregate_results={
                'perplexity': perplexity,
                'avg_log_likelihood': avg_log_likelihood
            }
        )


class F1ScoreMetric(EvaluationMetric):
    def __init__(self):
        super().__init__(
            name="f1_score",
            greater_is_better=True,
            long_name="F1 Score",
            metric_details="Computes F1 score (harmonic mean of precision and recall)"
        )
    
    def eval_fn(
        self,
        predictions: pd.Series,
        targets: Optional[pd.Series] = None,
        metrics: Optional[Dict[str, MetricValue]] = None,
        **kwargs
    ) -> MetricValue:
        if targets is None:
            return MetricValue(aggregate_results={'f1_score': 0.0})
        
        tp = ((predictions == 1) & (targets == 1)).sum()
        fp = ((predictions == 1) & (targets == 0)).sum()
        fn = ((predictions == 0) & (targets == 1)).sum()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return MetricValue(
            aggregate_results={
                'f1_score': f1,
                'precision': precision,
                'recall': recall,
                'true_positives': int(tp),
                'false_positives': int(fp),
                'false_negatives': int(fn)
            }
        )


class CustomMetric(EvaluationMetric):
    def __init__(
        self,
        name: str,
        eval_function: Callable,
        greater_is_better: bool = True,
        long_name: Optional[str] = None,
        metric_details: Optional[str] = None
    ):
        super().__init__(
            name=name,
            greater_is_better=greater_is_better,
            long_name=long_name,
            metric_details=metric_details
        )
        self._eval_function = eval_function
    
    def eval_fn(
        self,
        predictions: pd.Series,
        targets: Optional[pd.Series] = None,
        metrics: Optional[Dict[str, MetricValue]] = None,
        **kwargs
    ) -> MetricValue:
        result = self._eval_function(predictions, targets, metrics, **kwargs)
        
        if isinstance(result, MetricValue):
            return result
        elif isinstance(result, dict):
            return MetricValue(aggregate_results=result)
        else:
            return MetricValue(aggregate_results={'score': float(result)})


def make_metric(
    name: str,
    eval_fn: Callable,
    greater_is_better: bool = True,
    long_name: Optional[str] = None,
    metric_details: Optional[str] = None
) -> EvaluationMetric:
    return CustomMetric(
        name=name,
        eval_function=eval_fn,
        greater_is_better=greater_is_better,
        long_name=long_name,
        metric_details=metric_details
    )


def elo_rating(k_factor: int = 32, initial_rating: float = 1500) -> ELORatingMetric:
    return ELORatingMetric(k_factor=k_factor, initial_rating=initial_rating)


def win_rate() -> WinRateMetric:
    return WinRateMetric()


def accuracy() -> AccuracyMetric:
    return AccuracyMetric()


def latency() -> LatencyMetric:
    return LatencyMetric()


def perplexity() -> PerplexityMetric:
    return PerplexityMetric()


def f1_score() -> F1ScoreMetric:
    return F1ScoreMetric()


class MetricsLogger:
    def __init__(self):
        self.metrics: Dict[str, EvaluationMetric] = {}
        self.metric_history: Dict[str, List[MetricValue]] = {}
    
    def register_metric(self, metric: EvaluationMetric):
        self.metrics[metric.name] = metric
        if metric.name not in self.metric_history:
            self.metric_history[metric.name] = []
    
    def log_metric_value(self, metric_name: str, value: MetricValue):
        if metric_name in self.metrics:
            self.metric_history[metric_name].append(value)
    
    def get_metric(self, name: str) -> Optional[EvaluationMetric]:
        return self.metrics.get(name)
    
    def get_metric_history(self, name: str) -> List[MetricValue]:
        return self.metric_history.get(name, [])
    
    def evaluate(
        self,
        metric_name: str,
        predictions: pd.Series,
        targets: Optional[pd.Series] = None,
        **kwargs
    ) -> Optional[MetricValue]:
        metric = self.get_metric(metric_name)
        if metric:
            result = metric.compute(predictions, targets, **kwargs)
            self.log_metric_value(metric_name, result)
            return result
        return None
