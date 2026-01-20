"""
Complete workflow example demonstrating the Model Arena platform.

This script shows how to:
1. Create a team and users
2. Register models from HuggingFace
3. Create and rent an arena
4. Run a tournament
5. Monitor performance metrics
"""

import httpx
import asyncio
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class ModelArenaClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def close(self):
        await self.client.aclose()
    
    async def create_user(self, email: str, name: str) -> Dict[str, Any]:
        """Create a new user."""
        response = await self.client.post(
            f"{self.base_url}/team_service/users",
            params={"email": email, "name": name}
        )
        response.raise_for_status()
        return response.json()
    
    async def create_team(self, name: str, description: str, owner_email: str) -> Dict[str, Any]:
        """Create a new team."""
        response = await self.client.post(
            f"{self.base_url}/team_service/teams",
            json={
                "name": name,
                "description": description,
                "owner_email": owner_email
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def add_credits(self, team_id: str, amount: float) -> Dict[str, Any]:
        """Add credits to a team."""
        response = await self.client.post(
            f"{self.base_url}/team_service/teams/{team_id}/credits",
            params={"amount": amount}
        )
        response.raise_for_status()
        return response.json()
    
    async def register_model(
        self,
        name: str,
        team_id: str,
        huggingface_model_id: str,
        description: str = "",
        tags: list = None
    ) -> Dict[str, Any]:
        """Register a model from HuggingFace."""
        response = await self.client.post(
            f"{self.base_url}/model_registry/models/register",
            json={
                "name": name,
                "team_id": team_id,
                "huggingface_model_id": huggingface_model_id,
                "description": description,
                "tags": tags or []
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def create_arena(
        self,
        name: str,
        description: str,
        arena_type: str,
        owner_team_id: str,
        rental_price: float = 10.0,
        evaluation_metrics: list = None
    ) -> Dict[str, Any]:
        """Create a new arena."""
        response = await self.client.post(
            f"{self.base_url}/arena_service/arenas",
            json={
                "name": name,
                "description": description,
                "arena_type": arena_type,
                "owner_team_id": owner_team_id,
                "rental_price_per_hour": rental_price,
                "evaluation_metrics": evaluation_metrics or ["accuracy", "latency"],
                "tags": ["benchmark"]
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def rent_arena(self, arena_id: str, team_id: str, duration_hours: int) -> Dict[str, Any]:
        """Rent an arena."""
        response = await self.client.post(
            f"{self.base_url}/arena_service/arenas/rent",
            json={
                "arena_id": arena_id,
                "team_id": team_id,
                "duration_hours": duration_hours
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def create_tournament(
        self,
        name: str,
        arena_id: str,
        team_id: str,
        model_ids: list,
        tournament_type: str = "round_robin"
    ) -> Dict[str, Any]:
        """Create a tournament."""
        response = await self.client.post(
            f"{self.base_url}/tournament_service/tournaments",
            json={
                "name": name,
                "arena_id": arena_id,
                "team_id": team_id,
                "model_ids": model_ids,
                "tournament_type": tournament_type
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def start_tournament(self, tournament_id: str) -> Dict[str, Any]:
        """Start a tournament."""
        response = await self.client.post(
            f"{self.base_url}/tournament_service/tournaments/{tournament_id}/start"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_tournament_standings(self, tournament_id: str) -> Dict[str, Any]:
        """Get tournament standings."""
        response = await self.client.get(
            f"{self.base_url}/tournament_service/tournaments/{tournament_id}/standings"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_model_performance(self, model_id: str) -> Dict[str, Any]:
        """Get model performance metrics."""
        response = await self.client.get(
            f"{self.base_url}/monitoring_service/metrics/model/{model_id}/performance"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_leaderboard(self, limit: int = 10) -> Dict[str, Any]:
        """Get global leaderboard."""
        response = await self.client.get(
            f"{self.base_url}/monitoring_service/metrics/leaderboard",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()


async def main():
    """Run the complete workflow."""
    client = ModelArenaClient()
    
    try:
        print("=" * 80)
        print("MODEL ARENA PLATFORM - COMPLETE WORKFLOW DEMO")
        print("=" * 80)
        
        # Step 1: Create users and team
        print("\n[1] Creating users and team...")
        user1 = await client.create_user("alice@example.com", "Alice")
        print(f"✓ Created user: {user1['name']} ({user1['email']})")
        
        team = await client.create_team(
            name="AI Research Lab",
            description="Our cutting-edge AI research team",
            owner_email="alice@example.com"
        )
        print(f"✓ Created team: {team['name']} (ID: {team['team_id']})")
        
        # Step 2: Add credits to team
        print("\n[2] Adding credits to team...")
        credits_result = await client.add_credits(team['team_id'], 1000.0)
        print(f"✓ Added credits. New balance: ${credits_result['new_balance']}")
        
        # Step 3: Register models from HuggingFace
        print("\n[3] Registering models from HuggingFace...")
        models = []
        
        model_configs = [
            {
                "name": "GPT-2 Small",
                "huggingface_model_id": "gpt2",
                "description": "OpenAI GPT-2 small model",
                "tags": ["language-model", "gpt2"]
            },
            {
                "name": "DistilGPT-2",
                "huggingface_model_id": "distilgpt2",
                "description": "Distilled version of GPT-2",
                "tags": ["language-model", "distilled"]
            },
            {
                "name": "GPT-2 Medium",
                "huggingface_model_id": "gpt2-medium",
                "description": "OpenAI GPT-2 medium model",
                "tags": ["language-model", "gpt2"]
            }
        ]
        
        for config in model_configs:
            model = await client.register_model(
                name=config["name"],
                team_id=team['team_id'],
                huggingface_model_id=config["huggingface_model_id"],
                description=config["description"],
                tags=config["tags"]
            )
            models.append(model)
            print(f"✓ Registered model: {model['name']} (ID: {model['model_id']})")
        
        # Step 4: Create an arena
        print("\n[4] Creating benchmark arena...")
        arena = await client.create_arena(
            name="Text Generation Benchmark",
            description="Comprehensive text generation quality assessment",
            arena_type="benchmark",
            owner_team_id=team['team_id'],
            rental_price=25.0,
            evaluation_metrics=["perplexity", "bleu", "rouge", "coherence"]
        )
        print(f"✓ Created arena: {arena['name']} (ID: {arena['arena_id']})")
        
        # Step 5: Rent the arena
        print("\n[5] Renting arena for tournament...")
        rental = await client.rent_arena(
            arena_id=arena['arena_id'],
            team_id=team['team_id'],
            duration_hours=3
        )
        print(f"✓ Rented arena for {rental['end_time']}")
        print(f"  Cost: ${rental['total_cost']}")
        
        # Step 6: Create a tournament
        print("\n[6] Creating Round Robin tournament...")
        tournament = await client.create_tournament(
            name="LLM Showdown 2024",
            arena_id=arena['arena_id'],
            team_id=team['team_id'],
            model_ids=[m['model_id'] for m in models],
            tournament_type="round_robin"
        )
        print(f"✓ Created tournament: {tournament['name']} (ID: {tournament['tournament_id']})")
        print(f"  Type: {tournament['tournament_type']}")
        print(f"  Models: {len(tournament['model_ids'])}")
        print(f"  Total rounds: {tournament['total_rounds']}")
        
        # Step 7: Start the tournament
        print("\n[7] Starting tournament...")
        start_result = await client.start_tournament(tournament['tournament_id'])
        print(f"✓ Tournament started: {start_result['message']}")
        
        # Step 8: Wait for tournament to complete (simulated)
        print("\n[8] Waiting for tournament to complete...")
        print("  (Matches are being executed in the background...)")
        await asyncio.sleep(5)  # In production, this would be longer
        
        # Step 9: Get tournament standings
        print("\n[9] Fetching tournament standings...")
        standings = await client.get_tournament_standings(tournament['tournament_id'])
        print(f"\n{'='*80}")
        print(f"TOURNAMENT STANDINGS - {tournament['name']}")
        print(f"{'='*80}")
        print(f"{'Rank':<6} {'Model ID':<38} {'Points':<8} {'W-L-D'}")
        print(f"{'-'*80}")
        
        for rank, (model_id, stats) in enumerate(standings['standings'], 1):
            wld = f"{stats['wins']}-{stats['losses']}-{stats['draws']}"
            print(f"{rank:<6} {model_id:<38} {stats['points']:<8} {wld}")
        
        # Step 10: Get individual model performance
        print(f"\n{'='*80}")
        print("INDIVIDUAL MODEL PERFORMANCE")
        print(f"{'='*80}")
        
        for model in models:
            try:
                perf = await client.get_model_performance(model['model_id'])
                print(f"\n{model['name']}:")
                print(f"  Total Matches: {perf['total_matches']}")
                print(f"  Win Rate: {perf['win_rate']:.2%}")
                print(f"  Record: {perf['wins']}W - {perf['losses']}L - {perf['draws']}D")
                print(f"  Trend: {perf['performance_trend']}")
            except Exception as e:
                print(f"  (Performance data not yet available)")
        
        # Step 11: Get global leaderboard
        print(f"\n{'='*80}")
        print("GLOBAL LEADERBOARD")
        print(f"{'='*80}")
        
        leaderboard = await client.get_leaderboard(limit=10)
        print(f"{'Rank':<6} {'Model ID':<38} {'Win Rate':<12} {'Matches'}")
        print(f"{'-'*80}")
        
        for rank, entry in enumerate(leaderboard['leaderboard'], 1):
            print(f"{rank:<6} {entry['model_id']:<38} {entry['win_rate']:.2%}      {entry['total_matches']}")
        
        print(f"\n{'='*80}")
        print("WORKFLOW COMPLETED SUCCESSFULLY!")
        print(f"{'='*80}")
        print(f"\nSummary:")
        print(f"  - Team created: {team['name']}")
        print(f"  - Models registered: {len(models)}")
        print(f"  - Arena created and rented: {arena['name']}")
        print(f"  - Tournament completed: {tournament['name']}")
        print(f"  - Total matches played: {len(standings['standings'])}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
