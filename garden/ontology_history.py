from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class OntologyHistoryEntry:
    """Records a single change to a model's ontology"""
    
    def __init__(
        self,
        previous_ontology: Optional[Dict[str, Any]],
        new_ontology: Optional[Dict[str, Any]],
        changed_by: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.entry_id = str(uuid.uuid4())
        self.timestamp = datetime.now()
        self.previous_ontology = previous_ontology
        self.new_ontology = new_ontology
        self.changed_by = changed_by or "system"
        self.reason = reason
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'entry_id': self.entry_id,
            'timestamp': self.timestamp.isoformat(),
            'previous_ontology': self.previous_ontology,
            'new_ontology': self.new_ontology,
            'changed_by': self.changed_by,
            'reason': self.reason,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OntologyHistoryEntry':
        entry = cls(
            previous_ontology=data.get('previous_ontology'),
            new_ontology=data.get('new_ontology'),
            changed_by=data.get('changed_by'),
            reason=data.get('reason'),
            metadata=data.get('metadata')
        )
        entry.entry_id = data.get('entry_id', entry.entry_id)
        if 'timestamp' in data:
            entry.timestamp = datetime.fromisoformat(data['timestamp'])
        return entry


class OntologyHistory:
    """Tracks the complete history of ontology changes for a model"""
    
    def __init__(self):
        self.entries: list[OntologyHistoryEntry] = []
    
    def add_entry(
        self,
        previous_ontology: Optional[Dict[str, Any]],
        new_ontology: Optional[Dict[str, Any]],
        changed_by: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OntologyHistoryEntry:
        """Add a new history entry"""
        entry = OntologyHistoryEntry(
            previous_ontology=previous_ontology,
            new_ontology=new_ontology,
            changed_by=changed_by,
            reason=reason,
            metadata=metadata
        )
        self.entries.append(entry)
        return entry
    
    def get_latest(self) -> Optional[OntologyHistoryEntry]:
        """Get the most recent history entry"""
        return self.entries[-1] if self.entries else None
    
    def get_by_id(self, entry_id: str) -> Optional[OntologyHistoryEntry]:
        """Get a specific history entry by ID"""
        for entry in self.entries:
            if entry.entry_id == entry_id:
                return entry
        return None
    
    def get_entries_since(self, timestamp: datetime) -> list[OntologyHistoryEntry]:
        """Get all entries after a given timestamp"""
        return [e for e in self.entries if e.timestamp > timestamp]
    
    def get_entries_by_user(self, changed_by: str) -> list[OntologyHistoryEntry]:
        """Get all entries by a specific user"""
        return [e for e in self.entries if e.changed_by == changed_by]
    
    def count(self) -> int:
        """Get total number of changes"""
        return len(self.entries)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_changes': len(self.entries),
            'entries': [e.to_dict() for e in self.entries]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OntologyHistory':
        history = cls()
        if 'entries' in data:
            history.entries = [
                OntologyHistoryEntry.from_dict(e) for e in data['entries']
            ]
        return history
