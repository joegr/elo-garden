import math
from typing import Dict, Tuple


class ELOSystem:
    def __init__(self, k_factor=32, initial_rating=1500):
        self.k_factor = k_factor
        self.initial_rating = initial_rating
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))
    
    def update_ratings(
        self,
        rating_a: float,
        rating_b: float,
        score_a: float,
        score_b: float = None
    ) -> Tuple[float, float]:
        if score_b is None:
            score_b = 1 - score_a
        
        expected_a = self.expected_score(rating_a, rating_b)
        expected_b = self.expected_score(rating_b, rating_a)
        
        new_rating_a = rating_a + self.k_factor * (score_a - expected_a)
        new_rating_b = rating_b + self.k_factor * (score_b - expected_b)
        
        return new_rating_a, new_rating_b
    
    def update_multi_player(
        self,
        ratings: Dict[str, float],
        scores: Dict[str, float]
    ) -> Dict[str, float]:
        new_ratings = {}
        player_ids = list(ratings.keys())
        
        for player_id in player_ids:
            total_change = 0
            player_rating = ratings[player_id]
            player_score = scores[player_id]
            
            for opponent_id in player_ids:
                if opponent_id == player_id:
                    continue
                
                opponent_rating = ratings[opponent_id]
                opponent_score = scores[opponent_id]
                
                expected = self.expected_score(player_rating, opponent_rating)
                
                if player_score > opponent_score:
                    actual = 1.0
                elif player_score < opponent_score:
                    actual = 0.0
                else:
                    actual = 0.5
                
                total_change += self.k_factor * (actual - expected)
            
            new_ratings[player_id] = player_rating + (total_change / (len(player_ids) - 1))
        
        return new_ratings
