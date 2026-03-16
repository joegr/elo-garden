"""
Garden SQLite Persistence Layer

Provides durable storage for all Garden state so nothing is lost on restart.
Single-file, zero-config, no external dependencies beyond stdlib.
"""

import sqlite3
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime


class GardenDB:
    def __init__(self, db_path: str = "garden_data/garden.db"):
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()
    
    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS models (
                model_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL DEFAULT '1.0',
                metadata TEXT DEFAULT '{}',
                ratings TEXT DEFAULT '{}',
                stats TEXT DEFAULT '{}',
                ontology TEXT,
                match_history TEXT DEFAULT '[]',
                created_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS arenas (
                arena_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                arena_type TEXT NOT NULL,
                higher_is_better INTEGER DEFAULT 1,
                metadata TEXT DEFAULT '{}',
                match_history TEXT DEFAULT '[]',
                created_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS matches (
                match_id TEXT PRIMARY KEY,
                model_a_id TEXT NOT NULL,
                model_b_id TEXT NOT NULL,
                arena_id TEXT NOT NULL,
                tournament_id TEXT,
                season_id TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                winner_id TEXT,
                scores TEXT DEFAULT '{}',
                rating_changes TEXT DEFAULT '{}',
                started_at TEXT,
                completed_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (model_a_id) REFERENCES models(model_id),
                FOREIGN KEY (model_b_id) REFERENCES models(model_id),
                FOREIGN KEY (arena_id) REFERENCES arenas(arena_id)
            );
            
            CREATE TABLE IF NOT EXISTS tournaments (
                tournament_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                arena_id TEXT NOT NULL,
                model_ids TEXT DEFAULT '[]',
                tournament_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                season_id TEXT,
                metadata TEXT DEFAULT '{}',
                standings TEXT DEFAULT '{}',
                match_ids TEXT DEFAULT '[]',
                created_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS seasons (
                season_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                arena_ids TEXT DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'active',
                metadata TEXT DEFAULT '{}',
                start_date TEXT,
                end_date TEXT,
                created_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS queue (
                queue_id TEXT PRIMARY KEY,
                model_a_id TEXT NOT NULL,
                model_b_id TEXT NOT NULL,
                arena_id TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'pending',
                match_id TEXT,
                result TEXT,
                error TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_matches_arena ON matches(arena_id);
            CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
            CREATE INDEX IF NOT EXISTS idx_queue_status ON queue(status);
            CREATE INDEX IF NOT EXISTS idx_queue_priority ON queue(priority DESC, created_at ASC);
        """)
        self.conn.commit()
    
    # ── Models ──────────────────────────────────────────────────────────
    
    def save_model(self, model_id: str, name: str, version: str,
                   metadata: Dict, ratings: Dict, stats: Dict,
                   ontology: Optional[Dict], match_history: List[str],
                   created_at: str):
        self.conn.execute("""
            INSERT OR REPLACE INTO models
            (model_id, name, version, metadata, ratings, stats, ontology, match_history, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            model_id, name, version,
            json.dumps(metadata), json.dumps(ratings), json.dumps(stats),
            json.dumps(ontology) if ontology else None,
            json.dumps(match_history), created_at
        ))
        self.conn.commit()
    
    def load_models(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM models").fetchall()
        return [self._row_to_model(r) for r in rows]
    
    def _row_to_model(self, row) -> Dict[str, Any]:
        return {
            'model_id': row['model_id'],
            'name': row['name'],
            'version': row['version'],
            'metadata': json.loads(row['metadata']),
            'ratings': json.loads(row['ratings']),
            'stats': json.loads(row['stats']),
            'ontology': json.loads(row['ontology']) if row['ontology'] else None,
            'match_history': json.loads(row['match_history']),
            'created_at': row['created_at'],
        }
    
    # ── Arenas ──────────────────────────────────────────────────────────
    
    def save_arena(self, arena_id: str, name: str, description: str,
                   arena_type: str, higher_is_better: bool,
                   metadata: Dict, match_history: List[str], created_at: str):
        self.conn.execute("""
            INSERT OR REPLACE INTO arenas
            (arena_id, name, description, arena_type, higher_is_better, metadata, match_history, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            arena_id, name, description, arena_type,
            1 if higher_is_better else 0,
            json.dumps(metadata), json.dumps(match_history), created_at
        ))
        self.conn.commit()
    
    def load_arenas(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM arenas").fetchall()
        return [self._row_to_arena(r) for r in rows]
    
    def _row_to_arena(self, row) -> Dict[str, Any]:
        return {
            'arena_id': row['arena_id'],
            'name': row['name'],
            'description': row['description'],
            'arena_type': row['arena_type'],
            'higher_is_better': bool(row['higher_is_better']),
            'metadata': json.loads(row['metadata']),
            'match_history': json.loads(row['match_history']),
            'created_at': row['created_at'],
        }
    
    # ── Matches ─────────────────────────────────────────────────────────
    
    def save_match(self, match_id: str, model_a_id: str, model_b_id: str,
                   arena_id: str, status: str, winner_id: Optional[str],
                   scores: Dict, rating_changes: Dict,
                   tournament_id: Optional[str], season_id: Optional[str],
                   started_at: Optional[str], completed_at: Optional[str],
                   created_at: str):
        self.conn.execute("""
            INSERT OR REPLACE INTO matches
            (match_id, model_a_id, model_b_id, arena_id, status, winner_id,
             scores, rating_changes, tournament_id, season_id,
             started_at, completed_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match_id, model_a_id, model_b_id, arena_id, status, winner_id,
            json.dumps(scores), json.dumps(rating_changes),
            tournament_id, season_id, started_at, completed_at, created_at
        ))
        self.conn.commit()
    
    def load_matches(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM matches").fetchall()
        return [self._row_to_match(r) for r in rows]
    
    def _row_to_match(self, row) -> Dict[str, Any]:
        return {
            'match_id': row['match_id'],
            'model_a_id': row['model_a_id'],
            'model_b_id': row['model_b_id'],
            'arena_id': row['arena_id'],
            'status': row['status'],
            'winner_id': row['winner_id'],
            'scores': json.loads(row['scores']),
            'rating_changes': json.loads(row['rating_changes']),
            'tournament_id': row['tournament_id'],
            'season_id': row['season_id'],
            'started_at': row['started_at'],
            'completed_at': row['completed_at'],
            'created_at': row['created_at'],
        }
    
    # ── Queue ───────────────────────────────────────────────────────────
    
    def save_queue_item(self, queue_id: str, model_a_id: str, model_b_id: str,
                        arena_id: str, priority: int, status: str,
                        match_id: Optional[str], result: Optional[Dict],
                        error: Optional[str], metadata: Dict,
                        created_at: str, started_at: Optional[str],
                        completed_at: Optional[str]):
        self.conn.execute("""
            INSERT OR REPLACE INTO queue
            (queue_id, model_a_id, model_b_id, arena_id, priority, status,
             match_id, result, error, metadata, created_at, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            queue_id, model_a_id, model_b_id, arena_id, priority, status,
            match_id, json.dumps(result) if result else None,
            error, json.dumps(metadata), created_at, started_at, completed_at
        ))
        self.conn.commit()
    
    def load_queue(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM queue WHERE status = ? ORDER BY priority DESC, created_at ASC",
                (status,)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM queue ORDER BY priority DESC, created_at ASC"
            ).fetchall()
        return [self._row_to_queue_item(r) for r in rows]
    
    def _row_to_queue_item(self, row) -> Dict[str, Any]:
        return {
            'queue_id': row['queue_id'],
            'model_a_id': row['model_a_id'],
            'model_b_id': row['model_b_id'],
            'arena_id': row['arena_id'],
            'priority': row['priority'],
            'status': row['status'],
            'match_id': row['match_id'],
            'result': json.loads(row['result']) if row['result'] else None,
            'error': row['error'],
            'metadata': json.loads(row['metadata']),
            'created_at': row['created_at'],
            'started_at': row['started_at'],
            'completed_at': row['completed_at'],
        }
    
    # ── Tournaments ─────────────────────────────────────────────────────
    
    def save_tournament(self, tournament_id: str, name: str, arena_id: str,
                        model_ids: List[str], tournament_type: str,
                        status: str, season_id: Optional[str],
                        metadata: Dict, standings: Dict,
                        match_ids: List[str], created_at: str):
        self.conn.execute("""
            INSERT OR REPLACE INTO tournaments
            (tournament_id, name, arena_id, model_ids, tournament_type,
             status, season_id, metadata, standings, match_ids, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tournament_id, name, arena_id,
            json.dumps(model_ids), tournament_type, status, season_id,
            json.dumps(metadata), json.dumps(standings),
            json.dumps(match_ids), created_at
        ))
        self.conn.commit()
    
    def load_tournaments(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM tournaments").fetchall()
        results = []
        for row in rows:
            results.append({
                'tournament_id': row['tournament_id'],
                'name': row['name'],
                'arena_id': row['arena_id'],
                'model_ids': json.loads(row['model_ids']),
                'tournament_type': row['tournament_type'],
                'status': row['status'],
                'season_id': row['season_id'],
                'metadata': json.loads(row['metadata']),
                'standings': json.loads(row['standings']),
                'match_ids': json.loads(row['match_ids']),
                'created_at': row['created_at'],
            })
        return results
    
    # ── Seasons ─────────────────────────────────────────────────────────
    
    def save_season(self, season_id: str, name: str, arena_ids: List[str],
                    status: str, metadata: Dict,
                    start_date: Optional[str], end_date: Optional[str],
                    created_at: str):
        self.conn.execute("""
            INSERT OR REPLACE INTO seasons
            (season_id, name, arena_ids, status, metadata, start_date, end_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            season_id, name, json.dumps(arena_ids), status,
            json.dumps(metadata), start_date, end_date, created_at
        ))
        self.conn.commit()
    
    def load_seasons(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM seasons").fetchall()
        results = []
        for row in rows:
            results.append({
                'season_id': row['season_id'],
                'name': row['name'],
                'arena_ids': json.loads(row['arena_ids']),
                'status': row['status'],
                'metadata': json.loads(row['metadata']),
                'start_date': row['start_date'],
                'end_date': row['end_date'],
                'created_at': row['created_at'],
            })
        return results
    
    # ── Utility ─────────────────────────────────────────────────────────
    
    def close(self):
        self.conn.close()
    
    def reset(self):
        """Drop all data. Use for testing only."""
        for table in ['queue', 'matches', 'tournaments', 'seasons', 'arenas', 'models']:
            self.conn.execute(f"DELETE FROM {table}")
        self.conn.commit()
