"""
Garden Arena Metrics

Only arena-relevant metrics live here: ELO rating computation and win rate.
Training metrics (accuracy, perplexity, F1, latency) belong in MLflow.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import math


@dataclass
class ArenaMetricResult:
    """Result of an arena metric computation"""
    values: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


def compute_elo_change(
    rating_a: float,
    rating_b: float,
    score_a: float,
    score_b: float,
    k_factor: int = 32
) -> tuple[float, float]:
    """Compute ELO rating changes for a single match.
    
    Returns (new_rating_a, new_rating_b).
    """
    expected_a = 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))
    expected_b = 1 / (1 + math.pow(10, (rating_a - rating_b) / 400))
    
    new_a = rating_a + k_factor * (score_a - expected_a)
    new_b = rating_b + k_factor * (score_b - expected_b)
    return new_a, new_b


def compute_win_rate(wins: int, total_matches: int) -> float:
    """Compute win rate as wins / total_matches."""
    return wins / total_matches if total_matches > 0 else 0.0


def compute_match_quality(rating_a: float, rating_b: float) -> float:
    """Compute match quality based on ELO proximity (0.0 to 1.0).
    
    Closer ratings = higher quality match for competitive evaluation.
    """
    diff = abs(rating_a - rating_b)
    return math.exp(-diff / 200)


def summarize_model_performance(
    stats: Dict[str, Any],
    ratings: Dict[str, float],
    initial_rating: float = 1500
) -> ArenaMetricResult:
    """Summarize a model's arena performance across all arenas."""
    ratings_list = list(ratings.values())
    avg_rating = sum(ratings_list) / len(ratings_list) if ratings_list else initial_rating
    max_rating = max(ratings_list) if ratings_list else initial_rating
    min_rating = min(ratings_list) if ratings_list else initial_rating
    
    return ArenaMetricResult(
        values={
            'average_rating': avg_rating,
            'highest_rating': max_rating,
            'lowest_rating': min_rating,
            'win_rate': compute_win_rate(stats.get('wins', 0), stats.get('total_matches', 0)),
            'total_matches': float(stats.get('total_matches', 0)),
        },
        metadata={
            'arenas_competed': len(ratings_list),
        }
    )
