# ELO Rating Integration in Garden

## Overview

The Garden platform now uses **ELO ratings as a central feature** for model indexing, matchmaking, and suggestions. ELO ratings are integrated throughout the system to ensure fair, competitive, and balanced matches.

## How ELO Works in Garden

### 1. **ELO System Core** (`garden/elo.py`)

- **K-factor**: 32 (default) - controls rating volatility
- **Initial rating**: 1500 (default) - starting point for all models
- **Rating calculation**: Standard ELO formula with expected score calculation
- **Multi-player support**: For tournaments with >2 participants

```python
from garden import Garden

garden = Garden(
    elo_k_factor=32,          # Rating change sensitivity
    initial_rating=1500       # Starting ELO for new models
)
```

### 2. **Per-Arena Ratings**

Models maintain **separate ELO ratings for each arena**:

```python
model = garden.models['model-id']
print(model.ratings)  # {'arena-1': 1650, 'arena-2': 1420, ...}

# Get rating for specific arena
rating = model.get_rating('arena-1', default=1500)

# Average rating across all arenas
avg = sum(model.ratings.values()) / len(model.ratings.values())
```

### 3. **Automatic Rating Updates**

After every match, ELO ratings update automatically:

```python
# Before match: Model A = 1500, Model B = 1500
match = garden.run_match(model_a, model_b, arena)

# After match (A wins): 
# Model A = 1516 (+16)
# Model B = 1484 (-16)

# Rating changes logged to MLflow automatically
```

## ELO-Based Matchmaking

### 1. **Enhanced Compatibility Scoring**

The ontology matcher now includes **ELO proximity** as 30% of compatibility score:

```python
from garden.ontology import OntologyMatcher

score = OntologyMatcher.calculate_compatibility(
    ontology1, ontology2,
    rating1=1600,      # Model 1's ELO
    rating2=1620,      # Model 2's ELO (close match!)
    elo_weight=0.3     # 30% weight for ELO proximity
)
```

**Scoring Breakdown:**
- Task type match: 35%
- Input compatibility: 15%
- Output compatibility: 15%
- Capability overlap: 7.5%
- Tag similarity: 7.5%
- **ELO proximity: 30%** ← NEW!

**ELO Proximity Formula:**
```
elo_similarity = e^(-|rating1 - rating2| / 200)
```

- Ratings within 100 points: ~60% similarity
- Ratings within 200 points: ~37% similarity
- Ratings within 400 points: ~14% similarity

### 2. **Find Compatible Models (ELO-Aware)**

```python
compatible = OntologyMatcher.find_compatible_models(
    target_ontology=model_ont,
    candidate_ontologies=all_ontologies,
    target_rating=1650,                    # Target's ELO
    candidate_ratings={'model-2': 1620},   # Candidates' ELOs
    min_score=0.5,
    elo_weight=0.3,
    prefer_close_ratings=True              # Prioritize similar ELO
)

# Returns: [(ontology, score), ...]
# Higher scores for models with similar ratings
```

### 3. **Find Best Opponent**

Find the most balanced matchup based on ELO:

```python
opponent = garden.find_best_matchup(
    model_id='my-model',
    arena_id='accuracy-arena',
    rating_tolerance=200,      # Max ELO difference
    min_matches=5              # Require experience
)

# Returns model with closest ELO rating
```

## ELO-Based Indexing & Search

### 1. **Get Models by ELO Range**

```python
# Get all models between 1400-1600 ELO
models = garden.get_models_by_elo_range(
    arena_id='accuracy-arena',  # Specific arena
    min_rating=1400,
    max_rating=1600
)

# Returns models sorted by rating (descending)
```

### 2. **ELO Leaderboard**

```python
# Top 10 models by ELO
leaderboard = garden.get_elo_leaderboard(
    arena_id='accuracy-arena',  # Or None for overall
    top_n=10
)

# Returns:
# [
#   {'model_id': '...', 'name': 'GPT-4', 'rating': 1750, ...},
#   {'model_id': '...', 'name': 'Claude', 'rating': 1720, ...},
#   ...
# ]
```

### 3. **Rating-Based Tiers**

Organize models into competitive tiers:

```python
# Elite tier (1700+)
elite = garden.get_models_by_elo_range(min_rating=1700)

# Advanced tier (1600-1700)
advanced = garden.get_models_by_elo_range(min_rating=1600, max_rating=1699)

# Intermediate tier (1500-1600)
intermediate = garden.get_models_by_elo_range(min_rating=1500, max_rating=1599)

# Beginner tier (<1500)
beginner = garden.get_models_by_elo_range(max_rating=1499)
```

## API Endpoints (ELO-Integrated)

### 1. **Get Compatible Models (ELO-Aware)**

```bash
POST /models/{model_id}/compatible?use_elo=true&arena_id=arena-1
{
  "min_score": 0.5
}

# Response includes ELO-adjusted compatibility scores
```

### 2. **ELO Leaderboard**

```bash
GET /models/elo/leaderboard?arena_id=arena-1&top_n=10

# Returns:
[
  {
    "model_id": "...",
    "name": "GPT-4",
    "rating": 1750,
    "total_matches": 50,
    "win_rate": 0.68
  },
  ...
]
```

### 3. **Get Models by ELO Range**

```bash
GET /models/elo/range?arena_id=arena-1&min_rating=1400&max_rating=1600

# Returns models within specified ELO range
```

### 4. **Find Best Opponent**

```bash
GET /models/{model_id}/best-opponent?arena_id=arena-1&rating_tolerance=200

# Returns:
{
  "model_id": "...",
  "name": "Claude",
  "rating": 1648,  # Close to your model's 1650
  "stats": {...}
}
```

## Frontend Integration

### 1. **Model Cards Show ELO**

Models display their ELO rating with color coding:

- **Yellow (1700+)**: Elite tier
- **Green (1600-1699)**: Advanced tier
- **Blue (1500-1599)**: Intermediate tier
- **Purple (1400-1499)**: Beginner tier
- **Gray (<1400)**: Novice tier

### 2. **Compatibility Suggestions Include ELO**

When you drag a model into the arena:
- Compatible models appear with **ELO ratings**
- Shows **ELO difference** (Δ) between models
- Higher compatibility for closer ratings

```
┌─────────────────────────────┐
│ GPT-Mini            1620    │
│ Match: 85% | ELO Δ: 30 pts │
└─────────────────────────────┘
```

### 3. **ELO-Based Match Suggestions**

The system automatically suggests balanced matchups:
1. **Ontology compatibility** (task type, I/O)
2. **ELO proximity** (fair competition)
3. **Combined score** for best matches

## MLflow Integration

All ELO data is logged to MLflow:

```python
# Logged automatically for every match:
mlflow.log_metrics({
    'model_a_rating_before': 1500,
    'model_a_rating_after': 1516,
    'model_a_rating_change': +16,
    'model_b_rating_before': 1500,
    'model_b_rating_after': 1484,
    'model_b_rating_change': -16
})
```

View in MLflow UI:
- Rating evolution over time
- Compare rating changes across models
- Analyze rating distributions by arena

## Best Practices

### 1. **Balanced Matchmaking**

```python
# Good: Similar ratings (competitive match)
garden.run_match(
    model_a='rating-1550',
    model_b='rating-1530',  # Δ20 points
    arena='arena-1'
)

# Avoid: Mismatched ratings (unfair match)
garden.run_match(
    model_a='rating-1800',
    model_b='rating-1200',  # Δ600 points (unfair)
    arena='arena-1'
)
```

### 2. **Use ELO for Tournament Seeding**

```python
# Get models sorted by ELO
ranked_models = garden.get_elo_leaderboard(arena_id='arena-1', top_n=16)

# Create tournament with top models
tournament = garden.create_tournament(
    name="Elite Championship",
    arena_id='arena-1',
    model_ids=[m['model_id'] for m in ranked_models],
    tournament_type=TournamentType.SINGLE_ELIMINATION
)
```

### 3. **Rating Tolerance for Fair Matches**

```python
# Conservative: ±100 ELO (very balanced)
opponent = garden.find_best_matchup(
    model_id='my-model',
    rating_tolerance=100
)

# Moderate: ±200 ELO (balanced, recommended)
opponent = garden.find_best_matchup(
    model_id='my-model',
    rating_tolerance=200
)

# Permissive: ±400 ELO (may be unbalanced)
opponent = garden.find_best_matchup(
    model_id='my-model',
    rating_tolerance=400
)
```

## Rating Interpretation

| ELO Range | Tier | Description |
|-----------|------|-------------|
| 1800+ | Grandmaster | Top 1% models, exceptional performance |
| 1700-1799 | Elite | Top 5%, highly competitive |
| 1600-1699 | Advanced | Top 20%, strong performers |
| 1500-1599 | Intermediate | Average, baseline performance |
| 1400-1499 | Beginner | Below average, needs improvement |
| <1400 | Novice | Significant improvement needed |

**Note:** Rating distributions will evolve as more matches are played. Initial ratings start at 1500.

## Example: ELO-Driven Workflow

```python
from garden import Garden, ontology

# 1. Create garden with ELO system
garden = Garden(
    enable_mlflow_tracking=True,
    elo_k_factor=32,
    initial_rating=1500
)

# 2. Register models with ontologies
gpt = garden.register_model(
    "GPT-Mini",
    ontology=ontology.text_generation_ontology("gpt-mini")
)

# 3. Play matches (ELO updates automatically)
for _ in range(20):
    # Find balanced opponent
    opponent = garden.find_best_matchup(
        gpt.model_id,
        rating_tolerance=200
    )
    
    if opponent:
        garden.run_match(gpt.model_id, opponent.model_id, arena_id)

# 4. Check ELO progression
print(f"Current ELO: {gpt.get_rating(arena_id)}")

# 5. Get ELO-based leaderboard
leaderboard = garden.get_elo_leaderboard(arena_id)
print("Top Models:")
for rank, entry in enumerate(leaderboard, 1):
    print(f"{rank}. {entry['name']}: {entry['rating']:.0f}")
```

## Summary

**ELO is now central to Garden:**

✅ **Per-arena ratings** - Models tracked separately in each arena  
✅ **Automatic updates** - ELO changes after every match  
✅ **Compatibility matching** - 30% weight on ELO proximity  
✅ **Model indexing** - Search/filter by ELO range  
✅ **Best opponent finder** - Auto-match by rating  
✅ **Leaderboards** - Rank models by performance  
✅ **MLflow tracking** - All ratings logged  
✅ **Frontend display** - ELO shown on all model cards  

**ELO enables fair, competitive, and balanced matches across the platform!** 🎯
