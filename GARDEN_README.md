# Garden - Model Operations Framework

A comprehensive Python framework for managing competitive tournaments between AI models with ELO ratings, multiple arenas, seasons, and leaderboards.

## 🆕 MLflow Integration

**Garden v0.2.0** now includes MLflow-compatible tracking and custom metrics APIs! Use familiar MLflow patterns for experiment tracking while leveraging Garden's competitive evaluation features.

```python
from garden import Garden, tracking, metrics

# Enable MLflow-style tracking
garden = Garden(enable_mlflow_tracking=True)

# Use MLflow-compatible API
tracking.set_experiment("Model Comparison")
with tracking.start_run():
    tracking.log_params({"model": "GPT-Mini"})
    tracking.log_metrics({"accuracy": 0.95})

# Register custom metrics
garden.register_metric(metrics.elo_rating())
garden.register_metric(metrics.accuracy())
```

📖 **[Full MLflow Integration Guide →](MLFLOW_INTEGRATION.md)**

## Overview

**Garden** is a model operations (ModelOps) framework that enables you to:

- **Register and track multiple AI models**
- **Create competitive arenas** with custom benchmarks
- **Run matches** between models with automatic ELO rating updates
- **Organize tournaments** (Round Robin, Single Elimination, Swiss)
- **Manage seasons** across multiple arenas
- **Generate leaderboards** with comprehensive statistics
- **Persist state** for long-term tracking
- **🆕 MLflow-compatible tracking** for experiments and runs
- **🆕 Custom metrics** with EvaluationMetric API

## Architecture

### Core Components

1. **Garden** - Main orchestrator managing all components
2. **Model** - Represents an AI model with ratings and statistics
3. **Arena** - Virtual environment where models compete
4. **Match** - Individual competition between two models
5. **Tournament** - Organized competition with multiple matches
6. **Season** - Long-term tracking across multiple arenas
7. **Leaderboard** - Rankings and statistics display
8. **ELO System** - Rating calculation engine
9. **🆕 Tracking** - MLflow-compatible experiment tracking
10. **🆕 Metrics** - Custom evaluation metrics system

## Installation

```bash
# Install dependencies (pandas required for metrics)
pip install -r requirements.txt

# Or install minimal dependencies
pip install pandas numpy
```

## Quick Start

### Basic Example

```python
from garden import Garden, TournamentType

# Initialize Garden (with optional MLflow tracking)
garden = Garden(
    name="My Model Garden", 
    elo_k_factor=32, 
    initial_rating=1500,
    enable_mlflow_tracking=True  # Enable MLflow-style tracking
)

# Register models
model_a = garden.register_model(name="GPT-Mini", version="1.0")
model_b = garden.register_model(name="BERT-Tiny", version="1.0")

# Create a benchmark arena
def accuracy_benchmark(model, test_data=None):
    # Your benchmark logic here
    return 0.85  # Return a score

arena = garden.create_benchmark_arena(
    name="Accuracy Arena",
    benchmark_fn=accuracy_benchmark,
    higher_is_better=True
)

# Run a match
match = garden.run_match(
    model_a_id=model_a.model_id,
    model_b_id=model_b.model_id,
    arena_id=arena.arena_id
)

print(f"Winner: {match.result.winner_id}")
print(f"Ratings: {match.result.rating_changes}")

# Create and run a tournament
tournament = garden.create_tournament(
    name="Championship",
    arena_id=arena.arena_id,
    model_ids=[model_a.model_id, model_b.model_id],
    tournament_type=TournamentType.ROUND_ROBIN
)

garden.run_tournament(tournament.tournament_id)

# View leaderboard
leaderboard = garden.create_leaderboard(
    name="Overall Rankings",
    arena_id=arena.arena_id
)
print(leaderboard.format_table())
```

## Detailed Usage

### 1. Model Management

```python
# Register a model
model = garden.register_model(
    name="My Model",
    version="2.0",
    metadata={"architecture": "transformer", "params": "100M"}
)

# Access model information
print(f"Model ID: {model.model_id}")
print(f"Rating in arena: {model.get_rating(arena_id)}")
print(f"Win rate: {model.stats['win_rate']}")
print(f"Total matches: {model.stats['total_matches']}")
```

### 2. Arena Creation

**Benchmark Arena** (automatic winner determination):

```python
def my_benchmark(model, **kwargs):
    # Run your benchmark
    score = evaluate_model(model)
    return score

arena = garden.create_benchmark_arena(
    name="Performance Arena",
    benchmark_fn=my_benchmark,
    description="Measures model performance",
    higher_is_better=True  # or False for metrics like perplexity
)
```

**Custom Arena** (manual evaluation):

```python
from garden import CustomArena

def custom_evaluation(model_a, model_b, **kwargs):
    # Custom head-to-head evaluation
    return {
        'model_a_score': 0.85,
        'model_b_score': 0.78
    }

arena = CustomArena(
    name="Custom Arena",
    evaluation_fn=custom_evaluation
)
garden.register_arena(arena)
```

### 3. Running Matches

```python
# Single match
match = garden.run_match(
    model_a_id=model_a.model_id,
    model_b_id=model_b.model_id,
    arena_id=arena.arena_id,
    tournament_id=None,  # Optional
    season_id=None       # Optional
)

# Access match results
print(f"Status: {match.status}")
print(f"Winner: {match.result.winner_id}")
print(f"Scores: {match.result.scores}")
print(f"Rating changes: {match.result.rating_changes}")
```

### 4. Tournament Management

**Tournament Types:**
- `ROUND_ROBIN` - Every model plays every other model
- `SINGLE_ELIMINATION` - Single-elimination bracket
- `SWISS` - Swiss-system tournament
- `DOUBLE_ELIMINATION` - (Coming soon)

```python
# Create tournament
tournament = garden.create_tournament(
    name="Spring Championship",
    arena_id=arena.arena_id,
    model_ids=[model1.model_id, model2.model_id, model3.model_id],
    tournament_type=TournamentType.ROUND_ROBIN,
    season_id=season.season_id  # Optional
)

# Run tournament
garden.run_tournament(tournament.tournament_id)

# View standings
rankings = tournament.get_rankings()
for rank, (model_id, stats) in enumerate(rankings, start=1):
    print(f"{rank}. {model_id} - Points: {stats['points']}, W/L/D: {stats['wins']}/{stats['losses']}/{stats['draws']}")
```

### 5. Season Management

```python
# Create a season across multiple arenas
season = garden.create_season(
    name="2026 Championship Season",
    arena_ids=[arena1.arena_id, arena2.arena_id, arena3.arena_id],
    metadata={"year": 2026, "quarter": "Q1"}
)

# Start the season
season.start()

# Register models
for model in models:
    season.register_model(model.model_id)

# Create tournaments within the season
tournament = garden.create_tournament(
    name="Season Tournament",
    arena_id=arena1.arena_id,
    model_ids=[m.model_id for m in models],
    season_id=season.season_id
)

# View season leaderboard
leaderboard = season.get_overall_leaderboard()
for rank, (model_id, avg_rating) in enumerate(leaderboard, start=1):
    print(f"{rank}. {model_id}: {avg_rating:.1f}")
```

### 6. Leaderboards

```python
# Create arena-specific leaderboard
leaderboard = garden.create_leaderboard(
    name="Accuracy Leaderboard",
    arena_id=arena.arena_id
)

# Create season-wide leaderboard
season_leaderboard = garden.create_leaderboard(
    name="Season Leaderboard",
    season_id=season.season_id
)

# Display formatted table
print(leaderboard.format_table(top_n=10))

# Access specific data
top_3 = leaderboard.get_top_n(3)
model_rank = leaderboard.get_model_rank(model_id)
percentile = leaderboard.get_percentile(model_id)
```

### 7. ELO Rating System

The framework uses an ELO rating system to track model performance:

```python
# Configure ELO parameters
garden = Garden(
    elo_k_factor=32,      # Higher = more volatile ratings
    initial_rating=1500   # Starting rating for new models
)

# Ratings are automatically updated after each match
# Access current ratings
rating = model.get_rating(arena_id)

# View rating history through match results
for match_id in model.match_history:
    match = garden.matches[match_id]
    print(f"Match: {match.result.rating_changes}")
```

### 8. Persistence

```python
# Save current state
garden.save_state()  # Auto-generates filename
garden.save_state("my_garden_state.json")  # Custom filename

# State includes:
# - All models and their ratings
# - All arenas
# - All matches and results
# - All tournaments and standings
# - All seasons
# - All leaderboards
```

## Complete Example

See `garden_example.py` for a full working example that demonstrates:

- Registering 8 models
- Creating 3 different arenas (accuracy, perplexity, latency)
- Running a full season with multiple tournaments
- Generating and displaying leaderboards
- Saving state

Run it:

```bash
python garden_example.py
```

## CLI Usage

Garden includes a command-line interface:

```bash
# Register a model
python garden_cli.py register-model --name "GPT-4" --version "1.0"

# Create a tournament
python garden_cli.py create-tournament --name "Championship" \
    --arena ARENA_ID --models MODEL1,MODEL2,MODEL3

# Run a tournament
python garden_cli.py run-tournament --tournament TOURNAMENT_ID

# View leaderboard
python garden_cli.py leaderboard --arena ARENA_ID --top 10

# Show statistics
python garden_cli.py stats

# List entities
python garden_cli.py list models
```

## API Reference

### Garden

```python
Garden(name, elo_k_factor=32, initial_rating=1500, data_dir="garden_data")
```

**Methods:**
- `register_model(name, model_id, version, metadata)` → Model
- `register_arena(arena)` → Arena
- `create_benchmark_arena(name, benchmark_fn, ...)` → BenchmarkArena
- `create_season(name, arena_ids, ...)` → Season
- `create_tournament(name, arena_id, model_ids, ...)` → Tournament
- `run_match(model_a_id, model_b_id, arena_id, ...)` → Match
- `run_tournament(tournament_id)` → Tournament
- `create_leaderboard(name, arena_id, season_id)` → Leaderboard
- `save_state(filename)` → None
- `get_stats()` → Dict

### Model

```python
Model(name, model_id, version, metadata)
```

**Attributes:**
- `model_id` - Unique identifier
- `name` - Model name
- `version` - Version string
- `ratings` - Dict of arena_id → rating
- `stats` - Match statistics (wins, losses, draws, win_rate)
- `match_history` - List of match IDs

**Methods:**
- `get_rating(arena_id, default)` → float
- `set_rating(arena_id, rating)` → None
- `update_stats(result)` → None

### Arena

```python
BenchmarkArena(name, benchmark_fn, higher_is_better=True)
CustomArena(name, evaluation_fn)
```

**Methods:**
- `evaluate(model_a, model_b, **kwargs)` → Dict[str, float]
- `determine_winner(scores)` → str  # BenchmarkArena only

### Tournament

```python
Tournament(name, arena_id, model_ids, tournament_type, season_id)
```

**Types:**
- `TournamentType.ROUND_ROBIN`
- `TournamentType.SINGLE_ELIMINATION`
- `TournamentType.SWISS`

**Methods:**
- `generate_matches()` → List[Tuple[str, str]]
- `get_rankings()` → List[Tuple[str, Dict]]
- `start()`, `complete()`, `cancel()`

### Season

```python
Season(name, arena_ids, start_date, end_date)
```

**Methods:**
- `register_model(model_id)` → None
- `update_rating(arena_id, model_id, rating)` → None
- `get_arena_leaderboard(arena_id)` → List[Tuple[str, float]]
- `get_overall_leaderboard()` → List[Tuple[str, float]]

### Leaderboard

```python
Leaderboard(name, arena_id, season_id)
```

**Methods:**
- `update(model_ratings, model_stats)` → None
- `get_top_n(n)` → List[Dict]
- `get_model_rank(model_id)` → int
- `get_percentile(model_id)` → float
- `format_table(top_n)` → str

## Use Cases

### 1. Model Development
Track performance of model iterations across different benchmarks.

### 2. Model Selection
Compare multiple models to select the best for production.

### 3. Continuous Evaluation
Run ongoing tournaments to monitor model drift and performance.

### 4. Benchmark Standardization
Create standardized arenas for consistent model evaluation.

### 5. Research Competitions
Organize research competitions with automated scoring and rankings.

## Advanced Features

### Custom Scoring

```python
def custom_benchmark(model, test_data=None, **kwargs):
    # Complex evaluation logic
    accuracy = evaluate_accuracy(model, test_data)
    latency = measure_latency(model)
    
    # Composite score
    score = 0.7 * accuracy - 0.3 * (latency / 1000)
    return score
```

### Multi-Model Tournaments

```python
# Swiss-system for large model pools
tournament = garden.create_tournament(
    name="Swiss Tournament",
    arena_id=arena.arena_id,
    model_ids=list_of_100_models,
    tournament_type=TournamentType.SWISS
)
```

### Season-Long Tracking

```python
# Track models across multiple arenas over time
season = garden.create_season(
    name="Annual Championship",
    arena_ids=[accuracy_arena, speed_arena, quality_arena]
)

# Run monthly tournaments
for month in range(12):
    tournament = garden.create_tournament(
        name=f"Month {month+1} Tournament",
        arena_id=accuracy_arena,
        model_ids=active_models,
        season_id=season.season_id
    )
    garden.run_tournament(tournament.tournament_id)
```

## Best Practices

1. **Use meaningful arena names** - Makes leaderboards easier to understand
2. **Set appropriate K-factors** - Higher for volatile competitions, lower for stable rankings
3. **Regular state saves** - Persist data after important tournaments
4. **Consistent benchmarks** - Ensure benchmark functions are deterministic when possible
5. **Season organization** - Group related competitions into seasons for better tracking

## Extending Garden

### Custom Arena Types

```python
from garden.arena import Arena

class MyCustomArena(Arena):
    def evaluate(self, model_a, model_b, **kwargs):
        # Your custom evaluation logic
        return {
            'model_a_score': score_a,
            'model_b_score': score_b
        }
```

### Custom Tournament Types

Extend the `Tournament` class to implement new tournament formats.

## Troubleshooting

**Issue:** Ratings not updating
- Ensure matches are being run through `garden.run_match()`
- Check that arena evaluation returns valid scores

**Issue:** Tournament not generating matches
- Verify all model IDs exist in the garden
- Check tournament type is supported

**Issue:** Leaderboard empty
- Ensure models have participated in matches
- Call `garden.update_leaderboard()` to refresh

## MLflow Integration Features

Garden now supports MLflow-compatible APIs:

### Tracking API

```python
from garden import tracking

# Experiment management
tracking.create_experiment("Model Comparison")
tracking.set_experiment("Model Comparison")

# Run tracking
with tracking.start_run(run_name="baseline"):
    tracking.log_params({"model": "GPT", "size": "mini"})
    tracking.log_metrics({"accuracy": 0.95, "latency": 100})
    tracking.set_tags({"env": "prod"})

# Search runs
runs = tracking.search_runs()
```

### Custom Metrics

```python
from garden import metrics
import pandas as pd

# Use built-in metrics
elo_metric = metrics.elo_rating(k_factor=32)
acc_metric = metrics.accuracy()
latency_metric = metrics.latency()

# Register with Garden
garden.register_metric(elo_metric)
garden.register_metric(acc_metric)

# Create custom metrics
def custom_fn(predictions, targets, **kwargs):
    return {"score": (predictions == targets).mean()}

custom_metric = metrics.make_metric(
    name="my_metric",
    eval_fn=custom_fn,
    greater_is_better=True
)
```

### Automatic Match Tracking

When enabled, every match is automatically logged with:
- Parameters: model IDs, names, arena info
- Metrics: scores, ratings, rating changes
- Tags: winner, match type, arena type

See **[MLFLOW_INTEGRATION.md](MLFLOW_INTEGRATION.md)** for complete documentation.

## Future Enhancements

- [x] MLflow-compatible tracking API
- [x] Custom metrics system
- [ ] Double elimination tournaments
- [ ] Team-based competitions
- [ ] Time-series rating visualization
- [ ] Database backend (SQLite, PostgreSQL)
- [ ] Web dashboard
- [ ] REST API
- [ ] Match replay and analysis
- [ ] Automated scheduling
- [ ] MLflow UI integration

## Contributing

Garden is designed to be extensible. Key extension points:
- Custom arena types
- Tournament formats
- Rating systems
- Persistence backends

## License

MIT License

## Support

For issues and questions, please refer to the example files:
- `garden_example.py` - Complete working example
- `garden_cli.py` - Command-line interface usage
- `examples/mlflow_style_tracking.py` - MLflow integration example
- `MLFLOW_INTEGRATION.md` - Complete MLflow guide
