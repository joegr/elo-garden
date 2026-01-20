from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/model_arena")

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Team(Base):
    __tablename__ = "teams"
    
    team_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    credits = Column(Float, default=0.0)
    subscription_tier = Column(String, default="free")
    api_key = Column(String, unique=True)
    
    models = relationship("Model", back_populates="team")
    tournaments = relationship("Tournament", back_populates="team")
    rentals = relationship("ArenaRental", back_populates="team")

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    api_key = Column(String, unique=True)

class Model(Base):
    __tablename__ = "models"
    
    model_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    version = Column(String, default="1.0.0")
    team_id = Column(String, ForeignKey("teams.team_id"))
    huggingface_model_id = Column(String)
    model_type = Column(String, default="causal_lm")
    framework = Column(String, default="pytorch")
    description = Column(Text)
    tags = Column(JSON)
    parameters = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    status = Column(String, default="active")
    performance_metrics = Column(JSON)
    
    team = relationship("Team", back_populates="models")
    matches_as_a = relationship("Match", foreign_keys="Match.model_a_id", back_populates="model_a")
    matches_as_b = relationship("Match", foreign_keys="Match.model_b_id", back_populates="model_b")

class Arena(Base):
    __tablename__ = "arenas"
    
    arena_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    arena_type = Column(String, nullable=False)
    owner_team_id = Column(String, ForeignKey("teams.team_id"))
    rental_price_per_hour = Column(Float, default=0.0)
    status = Column(String, default="available")
    benchmark_config = Column(JSON)
    evaluation_metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    total_matches = Column(Integer, default=0)
    tags = Column(JSON)
    
    matches = relationship("Match", back_populates="arena")
    tournaments = relationship("Tournament", back_populates="arena")
    rentals = relationship("ArenaRental", back_populates="arena")

class ArenaRental(Base):
    __tablename__ = "arena_rentals"
    
    rental_id = Column(String, primary_key=True)
    arena_id = Column(String, ForeignKey("arenas.arena_id"))
    team_id = Column(String, ForeignKey("teams.team_id"))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    total_cost = Column(Float, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.now)
    
    arena = relationship("Arena", back_populates="rentals")
    team = relationship("Team", back_populates="rentals")

class Tournament(Base):
    __tablename__ = "tournaments"
    
    tournament_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    arena_id = Column(String, ForeignKey("arenas.arena_id"))
    team_id = Column(String, ForeignKey("teams.team_id"))
    model_ids = Column(JSON)
    tournament_type = Column(String, nullable=False)
    status = Column(String, default="scheduled")
    created_at = Column(DateTime, default=datetime.now)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    standings = Column(JSON)
    match_ids = Column(JSON)
    current_round = Column(Integer, default=0)
    total_rounds = Column(Integer, default=0)
    
    arena = relationship("Arena", back_populates="tournaments")
    team = relationship("Team", back_populates="tournaments")
    matches = relationship("Match", back_populates="tournament")

class Match(Base):
    __tablename__ = "matches"
    
    match_id = Column(String, primary_key=True)
    arena_id = Column(String, ForeignKey("arenas.arena_id"))
    tournament_id = Column(String, ForeignKey("tournaments.tournament_id"))
    model_a_id = Column(String, ForeignKey("models.model_id"))
    model_b_id = Column(String, ForeignKey("models.model_id"))
    status = Column(String, default="pending")
    winner = Column(String)
    model_a_score = Column(Float)
    model_b_score = Column(Float)
    benchmark_params = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    arena = relationship("Arena", back_populates="matches")
    tournament = relationship("Tournament", back_populates="matches")
    model_a = relationship("Model", foreign_keys=[model_a_id], back_populates="matches_as_a")
    model_b = relationship("Model", foreign_keys=[model_b_id], back_populates="matches_as_b")
    metrics = relationship("MatchMetric", back_populates="match")

class MatchMetric(Base):
    __tablename__ = "match_metrics"
    
    metric_id = Column(String, primary_key=True)
    match_id = Column(String, ForeignKey("matches.match_id"))
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    model_id = Column(String, ForeignKey("models.model_id"))
    timestamp = Column(DateTime, default=datetime.now)
    metadata = Column(JSON)
    
    match = relationship("Match", back_populates="metrics")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
