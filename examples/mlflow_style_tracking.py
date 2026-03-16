"""
Garden MLflow-Style Tracking Example

This example demonstrates how to use Garden's MLflow-compatible tracking API
to log experiments, runs, metrics, and custom evaluation metrics.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from garden import Garden, TournamentType
from garden import tracking, metrics
import pandas as pd
import random


def accuracy_benchmark(model, test_data=None):
    base_accuracy = 0.7
    model_variance = hash(model.model_id) % 100 / 1000
    random_factor = random.uniform(-0.05, 0.05)
    return base_accuracy + model_variance + random_factor


def latency_benchmark(model, test_data=None):
    base_latency = 100.0
    model_variance = hash(model.model_id) % 100 / 5
    random_factor = random.uniform(-10, 10)
    return base_latency + model_variance + random_factor


def main():
    print("=" * 80)
    print("Garden MLflow-Style Tracking Example")
    print("=" * 80)
    
    garden = Garden(
        name="MLflow Garden",
        elo_k_factor=32,
        initial_rating=1500,
        enable_mlflow_tracking=True,
        tracking_uri="./garden_mlruns"
    )
    
    tracker = garden.get_tracker()
    metrics_logger = garden.get_metrics_logger()
    
    print("\n1. Setting up Tracking Environment...")
    print(f"Tracking URI: {tracking.get_tracking_uri()}")
    
    experiment_id = tracking.create_experiment(
        name="Model Comparison Experiment",
        tags={"project": "model-evaluation", "version": "v1"}
    )
    print(f"Created experiment: {experiment_id}")
    
    print("\n2. Registering Custom Metrics...")
    elo_metric = metrics.elo_rating(k_factor=32, initial_rating=1500)
    win_rate_metric = metrics.win_rate()
    accuracy_metric = metrics.accuracy()
    latency_metric = metrics.latency()
    
    garden.register_metric(elo_metric)
    garden.register_metric(win_rate_metric)
    garden.register_metric(accuracy_metric)
    garden.register_metric(latency_metric)
    
    print("✓ Registered ELO Rating metric")
    print("✓ Registered Win Rate metric")
    print("✓ Registered Accuracy metric")
    print("✓ Registered Latency metric")
    
    print("\n3. Registering Models...")
    models = []
    model_names = ["GPT-Mini", "BERT-Tiny", "T5-Small", "RoBERTa-Base"]
    
    for name in model_names:
        model = garden.register_model(
            name=name,
            version="1.0",
            metadata={"architecture": "transformer", "params": f"{random.randint(10, 500)}M"}
        )
        models.append(model)
        print(f"  ✓ {model.name}")
    
    print("\n4. Creating Arenas...")
    accuracy_arena = garden.create_benchmark_arena(
        name="Accuracy Arena",
        benchmark_fn=accuracy_benchmark,
        description="Measures model accuracy",
        higher_is_better=True
    )
    
    latency_arena = garden.create_benchmark_arena(
        name="Latency Arena",
        benchmark_fn=latency_benchmark,
        description="Measures inference latency (lower is better)",
        higher_is_better=False
    )
    
    print(f"  ✓ {accuracy_arena.name}")
    print(f"  ✓ {latency_arena.name}")
    
    print("\n5. Running Matches with MLflow-Style Tracking...")
    
    tracking.set_experiment("Model Comparison Experiment")
    
    for i in range(5):
        model_a = random.choice(models)
        model_b = random.choice([m for m in models if m.model_id != model_a.model_id])
        
        match = garden.run_match(
            model_a_id=model_a.model_id,
            model_b_id=model_b.model_id,
            arena_id=accuracy_arena.arena_id
        )
        
        print(f"  Match {i+1}: {model_a.name} vs {model_b.name}")
        if match.result:
            winner = match.result.winner_id
            winner_name = garden.models[winner].name if winner else "Draw"
            print(f"    Winner: {winner_name}")
            print(f"    Scores: {match.result.scores}")
    
    print("\n6. Manual Run Context Example...")
    with tracker.run_context(run_name="custom_evaluation") as run:
        tracking.log_params({
            'experiment_type': 'manual_evaluation',
            'num_models': len(models),
            'evaluation_metric': 'accuracy'
        })
        
        tracking.log_metrics({
            'overall_accuracy': 0.85,
            'overall_latency': 95.3
        })
        
        tracking.set_tags({
            'environment': 'development',
            'dataset': 'test_set_v1'
        })
        
        print(f"  Run ID: {run.info.run_id}")
        print(f"  Run Name: {run.info.run_name}")
        print(f"  Logged params: {run.data.params}")
        print(f"  Logged metrics: {list(run.data.metrics.keys())}")
    
    print("\n7. Evaluating with Custom Metrics...")
    
    sample_predictions = pd.Series([1, 0, 1, 1, 0, 1, 0, 1])
    sample_targets = pd.Series([1, 0, 1, 0, 0, 1, 1, 1])
    
    acc_result = accuracy_metric.compute(sample_predictions, sample_targets)
    print(f"  Accuracy: {acc_result.aggregate_results}")
    
    sample_latencies = [95.2, 102.3, 98.7, 101.1, 99.5, 103.2, 97.8, 100.4]
    lat_result = latency_metric.compute(
        pd.Series([0] * len(sample_latencies)),
        latencies=sample_latencies
    )
    print(f"  Latency Stats: {lat_result.aggregate_results}")
    
    win_rate_result = win_rate_metric.compute(
        pd.Series([0]),
        wins=3,
        total_matches=5
    )
    print(f"  Win Rate: {win_rate_result.aggregate_results}")
    
    print("\n8. Searching Runs...")
    all_runs = tracking.search_runs(max_results=10)
    print(f"  Found {len(all_runs)} runs")
    
    for i, run in enumerate(all_runs[:3], 1):
        print(f"\n  Run {i}:")
        print(f"    ID: {run.info.run_id[:16]}...")
        print(f"    Name: {run.info.run_name}")
        print(f"    Status: {run.info.status}")
        print(f"    Params: {list(run.data.params.keys())[:5]}")
        print(f"    Metrics: {list(run.data.metrics.keys())[:5]}")
    
    print("\n9. Creating Tournament with Tracking...")
    tournament = garden.create_tournament(
        name="Championship",
        arena_id=accuracy_arena.arena_id,
        model_ids=[m.model_id for m in models],
        tournament_type=TournamentType.ROUND_ROBIN
    )
    
    garden.run_tournament(tournament.tournament_id)
    print(f"  ✓ Completed {len(tournament.match_ids)} matches")
    
    print("\n10. Tournament Standings:")
    print("=" * 60)
    for rank, (model_id, stats) in enumerate(tournament.get_rankings(), start=1):
        model_name = garden.models[model_id].name
        print(f"  {rank}. {model_name:<20} Points: {stats['points']:<3} "
              f"(W:{stats['wins']} L:{stats['losses']} D:{stats['draws']})")
    
    print("\n11. Viewing Model Statistics...")
    for model in models[:2]:
        print(f"\n  {model.name}:")
        print(f"    Overall Rating: {list(model.ratings.values())[0] if model.ratings else 1500:.1f}")
        print(f"    Win Rate: {model.stats['win_rate']*100:.1f}%")
        print(f"    Total Matches: {model.stats['total_matches']}")
        print(f"    W/L/D: {model.stats['wins']}/{model.stats['losses']}/{model.stats['draws']}")
    
    print("\n12. Creating Custom Metric...")
    
    def custom_score_fn(predictions, targets, metrics, **kwargs):
        threshold = kwargs.get('threshold', 0.5)
        above_threshold = (predictions > threshold).sum()
        return {
            'above_threshold_count': int(above_threshold),
            'above_threshold_pct': above_threshold / len(predictions) if len(predictions) > 0 else 0.0
        }
    
    custom_metric = metrics.make_metric(
        name="threshold_metric",
        eval_fn=custom_score_fn,
        greater_is_better=True,
        metric_details="Counts predictions above threshold"
    )
    
    garden.register_metric(custom_metric)
    
    test_preds = pd.Series([0.3, 0.7, 0.8, 0.2, 0.9, 0.4])
    custom_result = custom_metric.compute(test_preds, threshold=0.5)
    print(f"  Custom Metric Result: {custom_result.aggregate_results}")
    
    print("\n13. Saving State...")
    garden.save_state()
    tracker.save_state()
    
    print("\n" + "=" * 80)
    print("Garden MLflow-Style Tracking Demo Complete!")
    print("=" * 80)
    print(f"\nView tracking data in: {tracker.tracking_uri}")
    print(f"Total Experiments: {len(tracker.experiments)}")
    print(f"Total Runs: {len(tracker.runs)}")
    print(f"Registered Metrics: {len(metrics_logger.metrics)}")
    
    print("\nKey MLflow-Compatible Features:")
    print("  ✓ Experiment tracking")
    print("  ✓ Run management with context managers")
    print("  ✓ Parameter and metric logging")
    print("  ✓ Tag-based organization")
    print("  ✓ Custom metrics with EvaluationMetric")
    print("  ✓ Artifact management")
    print("  ✓ Run search and filtering")
    print("  ✓ Hierarchical experiment organization")


if __name__ == "__main__":
    main()
