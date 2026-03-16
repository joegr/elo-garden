from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class QueueStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueuedMatch:
    """Represents a match in the queue"""
    
    def __init__(
        self,
        model_a_id: str,
        model_b_id: str,
        arena_id: str,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.queue_id = str(uuid.uuid4())
        self.model_a_id = model_a_id
        self.model_b_id = model_b_id
        self.arena_id = arena_id
        self.priority = priority
        self.metadata = metadata or {}
        self.status = QueueStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.match_id: Optional[str] = None
        self.error: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'queue_id': self.queue_id,
            'model_a_id': self.model_a_id,
            'model_b_id': self.model_b_id,
            'arena_id': self.arena_id,
            'priority': self.priority,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'match_id': self.match_id,
            'error': self.error,
            'result': self.result,
            'metadata': self.metadata
        }


class ArenaQueue:
    """Manages a queue of matches to be executed"""
    
    def __init__(self):
        self.queue: List[QueuedMatch] = []
        self.history: List[QueuedMatch] = []
        self.max_history_size = 100
    
    def add_match(
        self,
        model_a_id: str,
        model_b_id: str,
        arena_id: str,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QueuedMatch:
        """Add a match to the queue"""
        queued_match = QueuedMatch(
            model_a_id=model_a_id,
            model_b_id=model_b_id,
            arena_id=arena_id,
            priority=priority,
            metadata=metadata
        )
        self.queue.append(queued_match)
        # Sort by priority (higher priority first), then by creation time
        self.queue.sort(key=lambda x: (-x.priority, x.created_at))
        return queued_match
    
    def get_next(self) -> Optional[QueuedMatch]:
        """Get the next pending match from the queue"""
        for match in self.queue:
            if match.status == QueueStatus.PENDING:
                return match
        return None
    
    def get_by_id(self, queue_id: str) -> Optional[QueuedMatch]:
        """Get a queued match by ID"""
        # Check active queue
        for match in self.queue:
            if match.queue_id == queue_id:
                return match
        # Check history
        for match in self.history:
            if match.queue_id == queue_id:
                return match
        return None
    
    def cancel_match(self, queue_id: str) -> bool:
        """Cancel a pending match"""
        match = self.get_by_id(queue_id)
        if match and match.status == QueueStatus.PENDING:
            match.status = QueueStatus.CANCELLED
            match.completed_at = datetime.now()
            self._move_to_history(match)
            return True
        return False
    
    def start_match(self, queue_id: str) -> bool:
        """Mark a match as running"""
        match = self.get_by_id(queue_id)
        if match and match.status == QueueStatus.PENDING:
            match.status = QueueStatus.RUNNING
            match.started_at = datetime.now()
            return True
        return False
    
    def complete_match(
        self,
        queue_id: str,
        match_id: str,
        result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Mark a match as completed"""
        match = self.get_by_id(queue_id)
        if match and match.status == QueueStatus.RUNNING:
            match.status = QueueStatus.COMPLETED
            match.completed_at = datetime.now()
            match.match_id = match_id
            match.result = result
            self._move_to_history(match)
            return True
        return False
    
    def fail_match(self, queue_id: str, error: str) -> bool:
        """Mark a match as failed"""
        match = self.get_by_id(queue_id)
        if match and match.status == QueueStatus.RUNNING:
            match.status = QueueStatus.FAILED
            match.completed_at = datetime.now()
            match.error = error
            self._move_to_history(match)
            return True
        return False
    
    def _move_to_history(self, match: QueuedMatch):
        """Move a match from queue to history"""
        if match in self.queue:
            self.queue.remove(match)
        if match not in self.history:
            self.history.append(match)
            # Keep history size limited
            if len(self.history) > self.max_history_size:
                self.history = self.history[-self.max_history_size:]
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status"""
        pending = sum(1 for m in self.queue if m.status == QueueStatus.PENDING)
        running = sum(1 for m in self.queue if m.status == QueueStatus.RUNNING)
        
        return {
            'total_queued': len(self.queue),
            'pending': pending,
            'running': running,
            'history_size': len(self.history)
        }
    
    def get_all_queued(self) -> List[Dict[str, Any]]:
        """Get all queued matches"""
        return [m.to_dict() for m in self.queue]
    
    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent match history"""
        return [m.to_dict() for m in self.history[-limit:]]
    
    def clear_queue(self):
        """Clear all pending matches"""
        for match in self.queue:
            if match.status == QueueStatus.PENDING:
                match.status = QueueStatus.CANCELLED
                match.completed_at = datetime.now()
                self._move_to_history(match)
