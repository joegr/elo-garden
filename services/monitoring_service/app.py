from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

app = FastAPI(title="Monitoring & Analytics Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MatchMetric(BaseModel):
    metric_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tournament_id: str
    match_id: str
    model_a_id: str
    model_b_id: str
    winner: str
    timestamp: datetime
    duration_seconds: Optional[float] = None
    model_a_metrics: Optional[Dict[str, float]] = None
    model_b_metrics: Optional[Dict[str, float]] = None

class PerformanceTimeSeries(BaseModel):
    model_id: str
    metric_name: str
    data_points: List[Dict[str, Any]]

class ModelPerformanceReport(BaseModel):
    model_id: str
    total_matches: int
    wins: int
    losses: int
    draws: int
    win_rate: float
    avg_score: float
    performance_trend: str
    last_updated: datetime

metrics_db: Dict[str, MatchMetric] = {}
model_performance_db: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
    "total_matches": 0,
    "wins": 0,
    "losses": 0,
    "draws": 0,
    "scores": [],
    "timestamps": [],
    "opponents": []
})

@app.get("/")
async def root():
    return {
        "service": "Monitoring & Analytics Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/metrics/match")
async def record_match_metric(metric: MatchMetric):
    metrics_db[metric.metric_id] = metric
    
    model_a_perf = model_performance_db[metric.model_a_id]
    model_b_perf = model_performance_db[metric.model_b_id]
    
    model_a_perf["total_matches"] += 1
    model_b_perf["total_matches"] += 1
    
    model_a_perf["timestamps"].append(metric.timestamp.isoformat())
    model_b_perf["timestamps"].append(metric.timestamp.isoformat())
    
    model_a_perf["opponents"].append(metric.model_b_id)
    model_b_perf["opponents"].append(metric.model_a_id)
    
    if metric.winner == "model_a":
        model_a_perf["wins"] += 1
        model_b_perf["losses"] += 1
    elif metric.winner == "model_b":
        model_b_perf["wins"] += 1
        model_a_perf["losses"] += 1
    else:
        model_a_perf["draws"] += 1
        model_b_perf["draws"] += 1
    
    if metric.model_a_metrics:
        for key, value in metric.model_a_metrics.items():
            if key not in model_a_perf:
                model_a_perf[key] = []
            model_a_perf[key].append(value)
    
    if metric.model_b_metrics:
        for key, value in metric.model_b_metrics.items():
            if key not in model_b_perf:
                model_b_perf[key] = []
            model_b_perf[key].append(value)
    
    return {"message": "Metric recorded successfully", "metric_id": metric.metric_id}

@app.get("/metrics/model/{model_id}/performance", response_model=ModelPerformanceReport)
async def get_model_performance(model_id: str):
    if model_id not in model_performance_db:
        raise HTTPException(status_code=404, detail="No performance data found for model")
    
    perf = model_performance_db[model_id]
    
    total_matches = perf["total_matches"]
    wins = perf["wins"]
    losses = perf["losses"]
    draws = perf["draws"]
    
    win_rate = wins / total_matches if total_matches > 0 else 0.0
    
    avg_score = 0.0
    if perf["scores"]:
        avg_score = sum(perf["scores"]) / len(perf["scores"])
    
    trend = calculate_performance_trend(perf)
    
    return ModelPerformanceReport(
        model_id=model_id,
        total_matches=total_matches,
        wins=wins,
        losses=losses,
        draws=draws,
        win_rate=win_rate,
        avg_score=avg_score,
        performance_trend=trend,
        last_updated=datetime.now()
    )

@app.get("/metrics/model/{model_id}/timeseries")
async def get_model_timeseries(
    model_id: str,
    metric_name: str = "win_rate",
    days: int = 30
):
    if model_id not in model_performance_db:
        raise HTTPException(status_code=404, detail="No performance data found for model")
    
    perf = model_performance_db[model_id]
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    data_points = []
    running_wins = 0
    running_total = 0
    
    for i, timestamp_str in enumerate(perf["timestamps"]):
        timestamp = datetime.fromisoformat(timestamp_str)
        
        if timestamp < cutoff_date:
            continue
        
        if i < len(perf.get("scores", [])):
            running_total += 1
            if i < perf["wins"]:
                running_wins += 1
            
            win_rate = running_wins / running_total if running_total > 0 else 0.0
            
            data_points.append({
                "timestamp": timestamp.isoformat(),
                "value": win_rate,
                "matches_played": running_total
            })
    
    return PerformanceTimeSeries(
        model_id=model_id,
        metric_name=metric_name,
        data_points=data_points
    )

@app.get("/metrics/tournament/{tournament_id}")
async def get_tournament_metrics(tournament_id: str):
    tournament_metrics = [
        m for m in metrics_db.values() 
        if m.tournament_id == tournament_id
    ]
    
    if not tournament_metrics:
        raise HTTPException(status_code=404, detail="No metrics found for tournament")
    
    model_stats = defaultdict(lambda: {"wins": 0, "losses": 0, "draws": 0})
    
    for metric in tournament_metrics:
        if metric.winner == "model_a":
            model_stats[metric.model_a_id]["wins"] += 1
            model_stats[metric.model_b_id]["losses"] += 1
        elif metric.winner == "model_b":
            model_stats[metric.model_b_id]["wins"] += 1
            model_stats[metric.model_a_id]["losses"] += 1
        else:
            model_stats[metric.model_a_id]["draws"] += 1
            model_stats[metric.model_b_id]["draws"] += 1
    
    return {
        "tournament_id": tournament_id,
        "total_matches": len(tournament_metrics),
        "model_statistics": dict(model_stats),
        "start_time": min(m.timestamp for m in tournament_metrics).isoformat(),
        "end_time": max(m.timestamp for m in tournament_metrics).isoformat()
    }

@app.get("/metrics/leaderboard")
async def get_global_leaderboard(
    metric: str = "win_rate",
    limit: int = 10
):
    leaderboard = []
    
    for model_id, perf in model_performance_db.items():
        total_matches = perf["total_matches"]
        if total_matches == 0:
            continue
        
        win_rate = perf["wins"] / total_matches
        
        leaderboard.append({
            "model_id": model_id,
            "win_rate": win_rate,
            "total_matches": total_matches,
            "wins": perf["wins"],
            "losses": perf["losses"],
            "draws": perf["draws"]
        })
    
    leaderboard.sort(key=lambda x: x["win_rate"], reverse=True)
    
    return {
        "metric": metric,
        "leaderboard": leaderboard[:limit],
        "total_models": len(leaderboard)
    }

@app.get("/metrics/compare")
async def compare_models(model_ids: str):
    model_id_list = model_ids.split(",")
    
    comparison = []
    
    for model_id in model_id_list:
        if model_id not in model_performance_db:
            continue
        
        perf = model_performance_db[model_id]
        total_matches = perf["total_matches"]
        
        comparison.append({
            "model_id": model_id,
            "total_matches": total_matches,
            "wins": perf["wins"],
            "losses": perf["losses"],
            "draws": perf["draws"],
            "win_rate": perf["wins"] / total_matches if total_matches > 0 else 0.0
        })
    
    return {
        "models": comparison,
        "comparison_date": datetime.now().isoformat()
    }

def calculate_performance_trend(perf: Dict[str, Any]) -> str:
    if perf["total_matches"] < 5:
        return "insufficient_data"
    
    recent_matches = min(5, perf["total_matches"])
    recent_wins = perf["wins"]
    
    if perf["total_matches"] > 10:
        older_half = perf["total_matches"] // 2
        recent_half = perf["total_matches"] - older_half
        
        recent_win_rate = recent_wins / recent_half if recent_half > 0 else 0
        
        if recent_win_rate > 0.6:
            return "improving"
        elif recent_win_rate < 0.4:
            return "declining"
        else:
            return "stable"
    
    return "stable"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
