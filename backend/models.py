import uuid
import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Union, Optional
from enum import Enum

class MetricType(str, Enum):
    COUNT = "COUNT"
    DURATION = "DURATION"
    BOOLEAN = "BOOLEAN"

class ResetPeriod(str, Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"

class TaskStatus(str, Enum):
    PENDING = "Pending"
    ACTIVE = "Active"
    DONE = "Done"

@dataclass
class Task:
    title: str
    subject: str
    difficulty: int  # 1-5
    energy_req: int  # 1-3
    deadline: str    # ISO 8601 Timestamp
    duration: int    # T_dur in minutes
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    notes: List[str] = field(default_factory=list)  # array of timestamped strings
    p_score: float = 0.0
    status: str = TaskStatus.PENDING.value
    parent_refs: List[str] = field(default_factory=list)  # Linked Goal/Project IDs
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "subject": self.subject,
            "notes": self.notes,
            "difficulty": self.difficulty,
            "energy_req": self.energy_req,
            "deadline": self.deadline,
            "duration": self.duration,
            "p_score": str(self.p_score) if self.p_score in (float('inf'), float('-inf')) else self.p_score,
            "status": self.status,
            "parent_refs": self.parent_refs,
            "created_at": self.created_at
        }
        
    @classmethod
    def from_dict(cls, data):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

@dataclass
class Goal:
    title: str
    category: str
    metric_type: str # MetricType
    target_value: Union[int, bool]
    current_value: Union[int, bool]
    reset_period: str # ResetPeriod
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    linked_subject: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "metric_type": self.metric_type,
            "target_value": self.target_value,
            "current_value": self.current_value,
            "reset_period": self.reset_period,
            "linked_subject": self.linked_subject,
            "last_updated": self.last_updated
        }
        
    @classmethod
    def from_dict(cls, data):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

@dataclass
class Project:
    name: str
    subject: str
    overall_notes: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_manifest: List[str] = field(default_factory=list) # Array of Task IDs
    goal_manifest: List[str] = field(default_factory=list) # Array of Goal IDs
    dependency_map: Dict[str, List[str]] = field(default_factory=dict) # Adjacency List
    completion_metric: float = 0.0 # Ratio

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "subject": self.subject,
            "overall_notes": self.overall_notes,
            "task_manifest": self.task_manifest,
            "goal_manifest": self.goal_manifest,
            "dependency_map": self.dependency_map,
            "completion_metric": self.completion_metric
        }
        
    @classmethod
    def from_dict(cls, data):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

@dataclass
class ActivityNode:
    action: str
    entity_id: str
    entity_type: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    next_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "timestamp": self.timestamp,
            "next_id": self.next_id
        }
        
    @classmethod
    def from_dict(cls, data):
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
