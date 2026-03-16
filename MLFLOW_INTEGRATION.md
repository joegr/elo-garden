# MLflow Integration Guide

Garden now provides MLflow-compatible tracking and custom metrics APIs, allowing you to use familiar MLflow patterns for experiment tracking, metric logging, and model evaluation.

## Overview

Garden's MLflow integration includes:

- **`garden.tracking`** - MLflow-compatible experiment and run tracking
- **`garden.metrics`** - Custom evaluation metrics similar to `mlflow.metrics`
- **Automatic tracking** - Matches and tournaments are automatically logged
- **Compatible APIs** - Use the same patterns as MLflow

## Quick Start

```python
from garden import Garden, TournamentType
from garden import tracking, metrics
import pandas as pd

# Initialize Garden with MLflow tracking enabled
garden = Garden(
    name="My Garden",
    enable_mlflow_tracking=True,
    tracking_uri="./mlruns"
)

# Access the tracker
tracker = garden.get_tracker()
```

## Core Concepts

### MLflow → Garden Mapping

| MLflow Concept | Garden Equivalent | Description |
|----------------|-------------------|-------------|
| **Experiment** | Tournament/Season | Groups of related runs |
| **Run** | Match | Individual model evaluation |
| **Metrics** | Scores, ELO ratings | Performance measurements |
| **Parameters** | Model metadata | Configuration values |
| **Artifacts** | Match results | Output files |

## Tracking API

### Setting Up Tracking

```python
from garden import tracking

# Set tracking URI
tracking.set_tracking_uri("./my_mlruns")

# Get current tracking URI
uri = tracking.get_tracking_uri()

# Create an experiment
experiment_id = tracking.create_experiment(
    name="Model Comparison",
    tags={"project": "llm-eval", "version": "v1"}
)

# Set active experiment
tracking.set_experiment("Model Comparison")
```

### Managing Runs

```python
# Start a run
run = tracking.start_run(run_name="baseline_evaluation")

# Log parameters
tracking.log_param("learning_rate", 0.001)
tracking.log_params({
    "batch_size": 32,
    "epochs": 10,
    "model_type": "transformer"
})

# Log metrics
tracking.log_metric("accuracy", 0.95, step=1)
tracking.log_metrics({
    "loss": 0.05,
    "f1_score": 0.93
}, step=1)

# Set tags
tracking.set_tag("environment", "production")
tracking.set_tags({
    "team": "ml-research",
    "priority": "high"
})

# End run
tracking.end_run(status="FINISHED")
```

### Using Context Managers

```python
# Recommended pattern
with tracker.run_context(run_name="experiment_1") as run:
    tracking.log_params({"alpha": 0.5})
    tracking.log_metrics({"score": 0.89})
    # Run automatically ends when context exits
```

### Searching Runs

```python
# Search all runs
runs = tracking.search_runs(
    experiment_ids=["exp_id_1", "exp_id_2"],
    max_results=100
)

# Get specific run
run = tracking.get_run("run_id_123")

# Access run data
print(run.info.run_name)
print(run.data.params)
print(run.data.metrics)
```

## Custom Metrics API

### Built-in Metrics

Garden provides several built-in evaluation metrics:

```python
from garden import metrics

# ELO Rating metric
elo_metric = metrics.elo_rating(k_factor=32, initial_rating=1500)

# Win Rate metric
win_rate_metric = metrics.win_rate()

# Accuracy metric
accuracy_metric = metrics.accuracy()

# Latency metric
latency_metric = metrics.latency()

# Perplexity metric
perplexity_metric = metrics.perplexity()

# F1 Score metric
f1_metric = metrics.f1_score()
```

### Registering Metrics

```python
# Register metrics with Garden
garden.register_metric(elo_metric)
garden.register_metric(accuracy_metric)
```

### Using Metrics

```python
import pandas as pd

# Prepare data
predictions = pd.Series([1, 0, 1, 1, 0])
targets = pd.Series([1, 0, 1, 0, 0])

# Compute metric
result = accuracy_metric.compute(predictions, targets)

# Access results
print(result.aggregate_results)  # {'accuracy': 0.8, 'correct': 4, 'total': 5}
print(result.scores)  # [1.0, 1.0, 1.0, 0.0, 1.0]
```

### Creating Custom Metrics

```python
from garden.metrics import make_metric, MetricValue

# Define custom evaluation function
def custom_eval_fn(predictions, targets, metrics, **kwargs):
    threshold = kwargs.get('threshold', 0.5)
    above_threshold = (predictions > threshold).sum()
    
    return MetricValue(
        scores=predictions.tolist(),
        aggregate_results={
            'count_above_threshold': int(above_threshold),
            'percentage': above_threshold / len(predictions)
        }
    )

# Create metric
custom_metric = make_metric(
    name="threshold_metric",
    eval_fn=custom_eval_fn,
    greater_is_better=True,
    metric_details="Counts predictions above threshold"
)

# Register and use
garden.register_metric(custom_metric)
result = custom_metric.compute(pd.Series([0.3, 0.7, 0.9]), threshold=0.5)
```

## Automatic Tracking

When `enable_mlflow_tracking=True`, Garden automatically tracks:

### Match Tracking

Every match automatically creates a run that logs:

**Parameters:**
- `model_a_id`, `model_b_id`
- `model_a_name`, `model_b_name`
- `arena_id`, `arena_name`
- `tournament_id`, `season_id`

**Metrics:**
- `model_a_score`, `model_b_score`
- `model_a_rating_before`, `model_b_rating_before`
- `model_a_rating_after`, `model_b_rating_after`
- `model_a_rating_change`, `model_b_rating_change`

**Tags:**
- `winner`: Winner ID or "draw"
- `match_type`: "tournament" or "standalone"
- `arena_type`: Arena class name

### Example

```python
from garden import Garden

# Initialize with tracking
garden = Garden(enable_mlflow_tracking=True)

# Register models
model_a = garden.register_model("GPT-Mini", version="1.0")
model_b = garden.register_model("BERT-Tiny", version="1.0")

# Create arena
def accuracy_fn(model):
    return 0.85  # Your evaluation logic

arena = garden.create_benchmark_arena(
    name="Accuracy Arena",
    benchmark_fn=accuracy_fn
)

# Run match - automatically tracked!
match = garden.run_match(
    model_a_id=model_a.model_id,
    model_b_id=model_b.model_id,
    arena_id=arena.arena_id
)

# Access tracking data
tracker = garden.get_tracker()
runs = tracker.search_runs()
print(f"Total runs logged: {len(runs)}")
```

## Advanced Features

### MetricValue Object

All metric evaluations return a `MetricValue` object:

```python
@dataclass
class MetricValue:
    scores: List[float]              # Per-row scores
    justifications: List[str]        # Optional explanations
    aggregate_results: Dict[str, float]  # Summary statistics
```

### EvaluationMetric Base Class

Create sophisticated metrics by extending `EvaluationMetric`:

```python
from garden.metrics import EvaluationMetric, MetricValue
import pandas as pd

class MyCustomMetric(EvaluationMetric):
    def __init__(self):
        super().__init__(
            name="my_metric",
            greater_is_better=True,
            long_name="My Custom Metric",
            metric_details="Detailed description"
        )
    
    def eval_fn(self, predictions, targets, metrics, **kwargs):
        # Your evaluation logic
        score = (predictions == targets).mean()
        
        return MetricValue(
            scores=predictions.tolist(),
            aggregate_results={'score': score}
        )

# Use it
metric = MyCustomMetric()
garden.register_metric(metric)
```

### Experiment Organization

Organize experiments hierarchically:

```python
# Create experiments for different tasks
exp1 = tracking.create_experiment("Accuracy Evaluation")
exp2 = tracking.create_experiment("Latency Benchmarks")
exp3 = tracking.create_experiment("Production Tests")

# Set active experiment
tracking.set_experiment("Accuracy Evaluation")

# Run evaluations
with tracker.run_context(run_name="baseline") as run:
    # Your evaluation code
    pass
```

## Integration with Tournaments

Tournaments automatically create experiments:

```python
from garden import TournamentType

# Create tournament
tournament = garden.create_tournament(
    name="Championship",
    arena_id=arena.arena_id,
    model_ids=[model1.model_id, model2.model_id],
    tournament_type=TournamentType.ROUND_ROBIN
)

# Run tournament - creates experiment "tournament_Championship"
garden.run_tournament(tournament.tournament_id)

# All matches tracked under this experiment
runs = tracking.search_runs()
```

## Comparison with MLflow

### Similarities

- ✅ Experiment and run management
- ✅ Parameter and metric logging
- ✅ Tag-based organization
- ✅ Custom metrics with `EvaluationMetric`
- ✅ Context managers for runs
- ✅ Artifact management
- ✅ Run search and filtering

### Differences

- **Domain-specific**: Garden focuses on model competition/evaluation
- **Automatic tracking**: Matches auto-logged without explicit calls
- **ELO ratings**: Built-in competitive rating system
- **Tournament support**: Native tournament and season management
- **Arena-based**: Evaluations organized by competitive arenas

### When to Use Garden vs MLflow

**Use Garden when:**
- Comparing multiple models competitively
- Running tournaments or seasons
- Tracking ELO ratings over time
- Need arena-based evaluation
- Want automatic match tracking

**Use MLflow when:**
- Training individual models
- Need model registry features
- Deploying models to production
- Require MLflow UI
- Integration with existing MLflow infrastructure

## Best Practices

### 1. Enable Tracking Selectively

```python
# Disable for quick tests
garden = Garden(enable_mlflow_tracking=False)

# Enable for production
garden = Garden(enable_mlflow_tracking=True)
```

### 2. Use Descriptive Names

```python
tracking.create_experiment("llm-accuracy-2024-q1")
with tracker.run_context(run_name="gpt_vs_bert_round1"):
    pass
```

### 3. Log Comprehensive Metadata

```python
tracking.log_params({
    'model_a_architecture': 'transformer',
    'model_a_params': '100M',
    'dataset': 'test_v2',
    'evaluation_date': '2024-01-15'
})
```

### 4. Register Metrics Early

```python
# Register all metrics at initialization
garden.register_metric(metrics.accuracy())
garden.register_metric(metrics.latency())
garden.register_metric(metrics.elo_rating())
```

### 5. Save State Regularly

```python
# Save both garden and tracking state
garden.save_state()
garden.get_tracker().save_state()
```

## API Reference

### garden.tracking

- `set_tracking_uri(uri: str)`
- `get_tracking_uri() -> str`
- `create_experiment(name, artifact_location, tags) -> str`
- `set_experiment(experiment_name) -> Experiment`
- `get_experiment(experiment_id) -> Experiment`
- `start_run(run_id, experiment_id, run_name, tags) -> Run`
- `end_run(status)`
- `active_run() -> Run`
- `log_param(key, value)`
- `log_params(params: dict)`
- `log_metric(key, value, step)`
- `log_metrics(metrics: dict, step)`
- `set_tag(key, value)`
- `set_tags(tags: dict)`
- `search_runs(experiment_ids, filter_string, max_results) -> List[Run]`
- `get_run(run_id) -> Run`

### garden.metrics

**Factory Functions:**
- `elo_rating(k_factor, initial_rating) -> ELORatingMetric`
- `win_rate() -> WinRateMetric`
- `accuracy() -> AccuracyMetric`
- `latency() -> LatencyMetric`
- `perplexity() -> PerplexityMetric`
- `f1_score() -> F1ScoreMetric`
- `make_metric(name, eval_fn, greater_is_better, ...) -> CustomMetric`

**Classes:**
- `EvaluationMetric` - Base class for metrics
- `MetricValue` - Metric result container
- `MetricsLogger` - Metric management

### Garden Methods

- `get_tracker() -> GardenTracker`
- `get_metrics_logger() -> MetricsLogger`
- `register_metric(metric: EvaluationMetric)`
- `evaluate_with_metric(metric_name, model_id, data, **kwargs)`

## Examples

See `examples/mlflow_style_tracking.py` for a comprehensive example demonstrating:

- Experiment creation and management
- Custom metric registration
- Automatic match tracking
- Manual run contexts
- Metric evaluation
- Run searching
- Tournament integration

## Migration from Pure MLflow

If you're using MLflow and want to add Garden:

```python
# Before (MLflow)
import mlflow
mlflow.set_experiment("my_experiment")
with mlflow.start_run():
    mlflow.log_param("alpha", 0.5)
    mlflow.log_metric("accuracy", 0.95)

# After (Garden with MLflow-style API)
from garden import tracking
tracking.set_experiment("my_experiment")
with tracking.start_run():
    tracking.log_param("alpha", 0.5)
    tracking.log_metric("accuracy", 0.95)

# Plus Garden-specific features
from garden import Garden
garden = Garden(enable_mlflow_tracking=True)
# Run competitive evaluations...
```

## Conclusion

Garden's MLflow integration provides a familiar interface for experiment tracking while adding powerful competitive evaluation features. Use it to track model tournaments, log custom metrics, and organize experiments just like MLflow, with the added benefit of automatic tracking and arena-based evaluation.
