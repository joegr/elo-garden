import argparse
import sys
from garden import Garden, TournamentType


def create_garden_cli():
    parser = argparse.ArgumentParser(
        description="Garden - Model Operations Framework CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Register a model
  python garden_cli.py register-model --name "GPT-4" --version "1.0"
  
  # Create an arena
  python garden_cli.py create-arena --name "Accuracy Arena" --type benchmark
  
  # Run a match
  python garden_cli.py run-match --model-a MODEL_ID_A --model-b MODEL_ID_B --arena ARENA_ID
  
  # Create and run a tournament
  python garden_cli.py create-tournament --name "Championship" --arena ARENA_ID --models MODEL1,MODEL2,MODEL3
  python garden_cli.py run-tournament --tournament TOURNAMENT_ID
  
  # View leaderboard
  python garden_cli.py leaderboard --arena ARENA_ID
  
  # Show stats
  python garden_cli.py stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    register_model_parser = subparsers.add_parser('register-model', help='Register a new model')
    register_model_parser.add_argument('--name', required=True, help='Model name')
    register_model_parser.add_argument('--version', default='1.0', help='Model version')
    register_model_parser.add_argument('--metadata', help='JSON metadata string')
    
    create_arena_parser = subparsers.add_parser('create-arena', help='Create a new arena')
    create_arena_parser.add_argument('--name', required=True, help='Arena name')
    create_arena_parser.add_argument('--type', choices=['benchmark', 'custom'], default='benchmark')
    create_arena_parser.add_argument('--description', default='', help='Arena description')
    
    run_match_parser = subparsers.add_parser('run-match', help='Run a match between two models')
    run_match_parser.add_argument('--model-a', required=True, help='First model ID')
    run_match_parser.add_argument('--model-b', required=True, help='Second model ID')
    run_match_parser.add_argument('--arena', required=True, help='Arena ID')
    run_match_parser.add_argument('--tournament', help='Tournament ID (optional)')
    run_match_parser.add_argument('--season', help='Season ID (optional)')
    
    create_tournament_parser = subparsers.add_parser('create-tournament', help='Create a tournament')
    create_tournament_parser.add_argument('--name', required=True, help='Tournament name')
    create_tournament_parser.add_argument('--arena', required=True, help='Arena ID')
    create_tournament_parser.add_argument('--models', required=True, help='Comma-separated model IDs')
    create_tournament_parser.add_argument('--type', choices=['round_robin', 'single_elimination', 'swiss'],
                                         default='round_robin', help='Tournament type')
    create_tournament_parser.add_argument('--season', help='Season ID (optional)')
    
    run_tournament_parser = subparsers.add_parser('run-tournament', help='Run a tournament')
    run_tournament_parser.add_argument('--tournament', required=True, help='Tournament ID')
    
    create_season_parser = subparsers.add_parser('create-season', help='Create a season')
    create_season_parser.add_argument('--name', required=True, help='Season name')
    create_season_parser.add_argument('--arenas', required=True, help='Comma-separated arena IDs')
    
    leaderboard_parser = subparsers.add_parser('leaderboard', help='Display leaderboard')
    leaderboard_parser.add_argument('--arena', help='Arena ID (optional)')
    leaderboard_parser.add_argument('--season', help='Season ID (optional)')
    leaderboard_parser.add_argument('--top', type=int, default=10, help='Number of top entries to show')
    
    subparsers.add_parser('stats', help='Show Garden statistics')
    
    list_parser = subparsers.add_parser('list', help='List entities')
    list_parser.add_argument('entity', choices=['models', 'arenas', 'tournaments', 'seasons', 'matches'])
    
    return parser


def main():
    parser = create_garden_cli()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    garden = Garden(name="Garden CLI")
    
    if args.command == 'register-model':
        import json
        metadata = json.loads(args.metadata) if args.metadata else None
        model = garden.register_model(
            name=args.name,
            version=args.version,
            metadata=metadata
        )
        print(f"✓ Model registered: {model.name}")
        print(f"  ID: {model.model_id}")
        print(f"  Version: {model.version}")
    
    elif args.command == 'create-arena':
        print(f"Arena creation requires custom benchmark function.")
        print(f"Please use the Python API for arena creation.")
        print(f"See garden_example.py for examples.")
    
    elif args.command == 'run-match':
        match = garden.run_match(
            model_a_id=args.model_a,
            model_b_id=args.model_b,
            arena_id=args.arena,
            tournament_id=args.tournament,
            season_id=args.season
        )
        print(f"✓ Match completed: {match.match_id}")
        if match.result:
            winner = match.result.winner_id or "Draw"
            print(f"  Winner: {winner}")
            print(f"  Scores: {match.result.scores}")
    
    elif args.command == 'create-tournament':
        model_ids = [m.strip() for m in args.models.split(',')]
        tournament_type = TournamentType[args.type.upper()]
        
        tournament = garden.create_tournament(
            name=args.name,
            arena_id=args.arena,
            model_ids=model_ids,
            tournament_type=tournament_type,
            season_id=args.season
        )
        print(f"✓ Tournament created: {tournament.name}")
        print(f"  ID: {tournament.tournament_id}")
        print(f"  Type: {tournament.tournament_type.value}")
        print(f"  Participants: {len(model_ids)}")
    
    elif args.command == 'run-tournament':
        tournament = garden.run_tournament(args.tournament)
        print(f"✓ Tournament completed: {tournament.name}")
        print(f"  Matches played: {len(tournament.match_ids)}")
        print(f"\nFinal Standings:")
        for rank, (model_id, stats) in enumerate(tournament.get_rankings(), start=1):
            print(f"  {rank}. {model_id[:8]}... - Points: {stats['points']}")
    
    elif args.command == 'create-season':
        arena_ids = [a.strip() for a in args.arenas.split(',')]
        season = garden.create_season(
            name=args.name,
            arena_ids=arena_ids
        )
        print(f"✓ Season created: {season.name}")
        print(f"  ID: {season.season_id}")
        print(f"  Arenas: {len(arena_ids)}")
    
    elif args.command == 'leaderboard':
        leaderboard = garden.create_leaderboard(
            name="CLI Leaderboard",
            arena_id=args.arena,
            season_id=args.season
        )
        print(leaderboard.format_table(top_n=args.top))
    
    elif args.command == 'stats':
        stats = garden.get_stats()
        print("\nGarden Statistics")
        print("=" * 60)
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title():<25} {value}")
        print("=" * 60)
    
    elif args.command == 'list':
        entity_map = {
            'models': garden.models,
            'arenas': garden.arenas,
            'tournaments': garden.tournaments,
            'seasons': garden.seasons,
            'matches': garden.matches
        }
        
        entities = entity_map[args.entity]
        print(f"\n{args.entity.title()} ({len(entities)} total):")
        print("=" * 60)
        
        for entity_id, entity in list(entities.items())[:20]:
            print(f"  {entity_id[:16]}... - {entity}")
        
        if len(entities) > 20:
            print(f"  ... and {len(entities) - 20} more")


if __name__ == '__main__':
    main()
