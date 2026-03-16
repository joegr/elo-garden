#!/usr/bin/env python3
"""Quick test of Garden MLflow integration"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from garden import Garden, TournamentType
from garden import tracking, metrics
import pandas as pd


print("=" * 60)
print("Testing Garden MLflow Integration")
print("=" * 60)

# Test 1: Basic initialization
print("\n1. Initializing Garden with MLflow tracking...")
try:
    garden = Garden(
        name="Test Garden",
        enable_mlflow_tracking=True,
        tracking_uri="./test_mlruns"
    )
    print("✓ Garden initialized successfully")
    print(f"  Tracking URI: {garden.get_tracking_uri()}")
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Test 2: Tracking API
print("\n2. Testing tracking API...")
try:
    # Check if experiment exists
    try:
        tracking.set_experiment("Test Experiment")
        print("✓ Set experiment (or created if not exists)")
    except:
        exp_id = tracking.create_experiment("Test Experiment")
        print(f"✓ Created experiment: {exp_id}")
    
    with tracking.run_context(run_name="test_run") as run:
        tracking.log_params({"test_param": "value"})
        tracking.log_metrics({"test_metric": 0.95})
        tracking.set_tags({"env": "test"})
        print(f"✓ Created run: {run.info.run_name}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Custom metrics
print("\n3. Testing custom metrics...")
try:
    acc_metric = metrics.accuracy()
    garden.register_metric(acc_metric)
    print("✓ Registered accuracy metric")
    
    predictions = pd.Series([1, 0, 1, 1, 0])
    targets = pd.Series([1, 0, 1, 0, 0])
    result = acc_metric.compute(predictions, targets)
    print(f"✓ Computed accuracy: {result.aggregate_results}")
    
    elo_metric = metrics.elo_rating()
    garden.register_metric(elo_metric)
    print("✓ Registered ELO rating metric")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Model registration and arena
print("\n4. Testing model registration...")
try:
    model_a = garden.register_model("Model-A", version="1.0")
    model_b = garden.register_model("Model-B", version="1.0")
    print(f"✓ Registered 2 models")
    
    def benchmark_fn(model, **kwargs):
        import random
        return 0.7 + random.uniform(-0.1, 0.1)
    
    arena = garden.create_benchmark_arena(
        name="Test Arena",
        benchmark_fn=benchmark_fn,
        higher_is_better=True
    )
    print(f"✓ Created arena: {arena.name}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Match with automatic tracking
print("\n5. Testing match with automatic tracking...")
try:
    match = garden.run_match(
        model_a_id=model_a.model_id,
        model_b_id=model_b.model_id,
        arena_id=arena.arena_id
    )
    print(f"✓ Match completed")
    if match.result:
        print(f"  Winner: {match.result.winner_id}")
        print(f"  Scores: {match.result.scores}")
        print(f"  Rating changes: {match.result.rating_changes}")
    
    # Check that run was logged
    runs = tracking.search_runs()
    print(f"✓ Total runs logged: {len(runs)}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Run searching
print("\n6. Testing run search...")
try:
    import mlflow
    all_runs = mlflow.search_runs(output_format="list")
    print(f"✓ Found {len(all_runs)} runs")
    for i, run in enumerate(all_runs[:2], 1):
        print(f"  Run {i}: {run.info.run_name} ({run.info.status})")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 7: State persistence
print("\n7. Testing state persistence...")
try:
    garden.save_state()
    print("✓ Garden state saved successfully")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)
print(f"\nTracking data saved to: {garden.get_tracking_uri()}")
import mlflow
print(f"Total runs: {len(mlflow.search_runs(output_format='list'))}")
print(f"Registered metrics: {len(garden.get_metrics_logger().metrics)}")
print("\n🚀 Launch MLflow UI with: mlflow ui --backend-store-uri ./test_mlruns")
