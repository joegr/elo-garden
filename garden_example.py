from garden import Garden, Model, TournamentType
import random


def accuracy_benchmark(model, test_data=None):
    base_accuracy = 0.7
    model_variance = hash(model.model_id) % 100 / 1000
    random_factor = random.uniform(-0.05, 0.05)
    
    return base_accuracy + model_variance + random_factor


def perplexity_benchmark(model, test_data=None):
    base_perplexity = 50.0
    model_variance = hash(model.model_id) % 100 / 10
    random_factor = random.uniform(-5, 5)
    
    return base_perplexity + model_variance + random_factor


def latency_benchmark(model, test_data=None):
    base_latency = 100.0
    model_variance = hash(model.model_id) % 100 / 5
    random_factor = random.uniform(-10, 10)
    
    return base_latency + model_variance + random_factor


def main():
    print("=" * 80)
    print("Garden Framework - Model Competition Example")
    print("=" * 80)
    
    garden = Garden(name="AI Model Garden", elo_k_factor=32, initial_rating=1500)
    
    print("\n1. Registering Models...")
    models = []
    model_names = [
        "GPT-Mini", "BERT-Tiny", "T5-Small", "RoBERTa-Base",
        "ALBERT-Large", "DistilBERT", "XLNet-Base", "ELECTRA-Small"
    ]
    
    for name in model_names:
        model = garden.register_model(
            name=name,
            version="1.0",
            metadata={"architecture": "transformer", "params": f"{random.randint(10, 500)}M"}
        )
        models.append(model)
        print(f"  ✓ Registered: {model.name} (ID: {model.model_id[:8]}...)")
    
    print(f"\nTotal models registered: {len(models)}")
    
    print("\n2. Creating Arenas...")
    accuracy_arena = garden.create_benchmark_arena(
        name="Accuracy Arena",
        benchmark_fn=accuracy_benchmark,
        description="Measures model accuracy on test dataset",
        higher_is_better=True
    )
    print(f"  ✓ Created: {accuracy_arena.name}")
    
    perplexity_arena = garden.create_benchmark_arena(
        name="Perplexity Arena",
        benchmark_fn=perplexity_benchmark,
        description="Measures model perplexity (lower is better)",
        higher_is_better=False
    )
    print(f"  ✓ Created: {perplexity_arena.name}")
    
    latency_arena = garden.create_benchmark_arena(
        name="Latency Arena",
        benchmark_fn=latency_benchmark,
        description="Measures inference latency in ms (lower is better)",
        higher_is_better=False
    )
    print(f"  ✓ Created: {latency_arena.name}")
    
    print("\n3. Creating Season...")
    season = garden.create_season(
        name="Spring 2026 Championship",
        arena_ids=[accuracy_arena.arena_id, perplexity_arena.arena_id, latency_arena.arena_id],
        metadata={"year": 2026, "quarter": "Q1"}
    )
    season.start()
    
    for model in models:
        season.register_model(model.model_id)
    
    print(f"  ✓ Created: {season.name}")
    print(f"  ✓ Registered {len(models)} models for the season")
    
    print("\n4. Creating Tournaments...")
    
    accuracy_tournament = garden.create_tournament(
        name="Accuracy Championship",
        arena_id=accuracy_arena.arena_id,
        model_ids=[m.model_id for m in models],
        tournament_type=TournamentType.ROUND_ROBIN,
        season_id=season.season_id
    )
    print(f"  ✓ Created: {accuracy_tournament.name} (Round Robin)")
    
    perplexity_tournament = garden.create_tournament(
        name="Perplexity Challenge",
        arena_id=perplexity_arena.arena_id,
        model_ids=[m.model_id for m in models],
        tournament_type=TournamentType.ROUND_ROBIN,
        season_id=season.season_id
    )
    print(f"  ✓ Created: {perplexity_tournament.name} (Round Robin)")
    
    print("\n5. Running Accuracy Tournament...")
    garden.run_tournament(accuracy_tournament.tournament_id)
    print(f"  ✓ Completed {len(accuracy_tournament.match_ids)} matches")
    
    print("\n6. Running Perplexity Tournament...")
    garden.run_tournament(perplexity_tournament.tournament_id)
    print(f"  ✓ Completed {len(perplexity_tournament.match_ids)} matches")
    
    print("\n7. Running Individual Matches in Latency Arena...")
    for i in range(10):
        model_a = random.choice(models)
        model_b = random.choice([m for m in models if m.model_id != model_a.model_id])
        
        match = garden.run_match(
            model_a_id=model_a.model_id,
            model_b_id=model_b.model_id,
            arena_id=latency_arena.arena_id,
            season_id=season.season_id
        )
        
        winner = "Draw" if match.result.winner_id is None else match.result.winner_id[:8]
        print(f"  Match {i+1}: {model_a.name} vs {model_b.name} -> Winner: {winner}")
    
    print("\n8. Creating Leaderboards...")
    
    accuracy_leaderboard = garden.create_leaderboard(
        name="Accuracy Leaderboard",
        arena_id=accuracy_arena.arena_id,
        season_id=season.season_id
    )
    
    perplexity_leaderboard = garden.create_leaderboard(
        name="Perplexity Leaderboard",
        arena_id=perplexity_arena.arena_id,
        season_id=season.season_id
    )
    
    overall_leaderboard = garden.create_leaderboard(
        name="Overall Season Leaderboard",
        season_id=season.season_id
    )
    
    print("  ✓ Created 3 leaderboards")
    
    print("\n9. Displaying Results...")
    
    print(accuracy_leaderboard.format_table(top_n=8))
    
    print(perplexity_leaderboard.format_table(top_n=8))
    
    print(overall_leaderboard.format_table(top_n=8))
    
    print("\n10. Tournament Standings...")
    print(f"\n{accuracy_tournament.name} - Final Standings:")
    print(f"{'='*60}")
    for rank, (model_id, stats) in enumerate(accuracy_tournament.get_rankings(), start=1):
        model_name = garden.models[model_id].name
        print(f"{rank}. {model_name:<20} Points: {stats['points']:<3} (W:{stats['wins']} L:{stats['losses']} D:{stats['draws']})")
    
    print("\n11. Garden Statistics...")
    stats = garden.get_stats()
    print(f"{'='*60}")
    print(f"Total Models:       {stats['total_models']}")
    print(f"Total Arenas:       {stats['total_arenas']}")
    print(f"Total Matches:      {stats['total_matches']}")
    print(f"Completed Matches:  {stats['completed_matches']}")
    print(f"Total Tournaments:  {stats['total_tournaments']}")
    print(f"Active Seasons:     {stats['active_seasons']}")
    print(f"{'='*60}")
    
    print("\n12. Saving Garden State...")
    garden.save_state()
    
    print("\n13. Model Details (Top 3)...")
    top_3 = overall_leaderboard.get_top_n(3)
    for entry in top_3:
        model = garden.models[entry['model_id']]
        print(f"\n{model.name}:")
        print(f"  Overall Rating: {entry['rating']:.1f}")
        print(f"  Win Rate: {entry['win_rate']*100:.1f}%")
        print(f"  Total Matches: {entry['total_matches']}")
        print(f"  Arena Ratings:")
        for arena_id, rating in model.ratings.items():
            arena_name = garden.arenas[arena_id].name
            print(f"    - {arena_name}: {rating:.1f}")
    
    print("\n" + "="*80)
    print("Garden Framework Demo Complete!")
    print("="*80)


if __name__ == "__main__":
    main()
