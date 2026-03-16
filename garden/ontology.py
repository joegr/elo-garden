"""
Model Ontology System for Garden

Defines input/output schemas for models to enable compatibility matching
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum


class DataType(Enum):
    """Supported data types for model I/O"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    TABULAR = "tabular"
    EMBEDDING = "embedding"
    JSON = "json"
    STRUCTURED = "structured"


class TaskType(Enum):
    """Common ML task types"""
    TEXT_GENERATION = "text_generation"
    TEXT_CLASSIFICATION = "text_classification"
    QUESTION_ANSWERING = "question_answering"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    IMAGE_CLASSIFICATION = "image_classification"
    OBJECT_DETECTION = "object_detection"
    IMAGE_GENERATION = "image_generation"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    TEXT_TO_SPEECH = "text_to_speech"
    EMBEDDING = "embedding"
    CUSTOM = "custom"


@dataclass
class IOSchema:
    """Schema defining input or output structure"""
    data_type: DataType
    shape: Optional[List[int]] = None  # For tensor-like data
    fields: Optional[Dict[str, str]] = None  # For structured data
    description: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None  # e.g., max_length, vocab_size
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'data_type': self.data_type.value,
            'shape': self.shape,
            'fields': self.fields,
            'description': self.description,
            'constraints': self.constraints
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IOSchema':
        return cls(
            data_type=DataType(data['data_type']),
            shape=data.get('shape'),
            fields=data.get('fields'),
            description=data.get('description'),
            constraints=data.get('constraints')
        )


@dataclass
class ModelOntology:
    """Complete ontology describing a model's capabilities"""
    model_id: str
    task_type: TaskType
    input_schema: IOSchema
    output_schema: IOSchema
    capabilities: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_id': self.model_id,
            'task_type': self.task_type.value,
            'input_schema': self.input_schema.to_dict(),
            'output_schema': self.output_schema.to_dict(),
            'capabilities': list(self.capabilities),
            'tags': list(self.tags),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelOntology':
        return cls(
            model_id=data.get('model_id', ''),
            task_type=TaskType(data['task_type']),
            input_schema=IOSchema.from_dict(data['input_schema']),
            output_schema=IOSchema.from_dict(data['output_schema']),
            capabilities=set(data.get('capabilities', [])),
            tags=set(data.get('tags', [])),
            metadata=data.get('metadata', {})
        )


class OntologyMatcher:
    """Matches models based on ontology compatibility and ELO ratings"""
    
    @staticmethod
    def calculate_compatibility(
        ont1: ModelOntology,
        ont2: ModelOntology,
        rating1: Optional[float] = None,
        rating2: Optional[float] = None,
        elo_weight: float = 0.3
    ) -> float:
        """
        Calculate compatibility score between two models (0.0 to 1.0)
        
        Args:
            ont1: First model ontology
            ont2: Second model ontology
            rating1: ELO rating for first model (optional)
            rating2: ELO rating for second model (optional)
            elo_weight: Weight for ELO similarity (0.0-1.0), default 0.3
        
        Returns:
            Compatibility score from 0.0 (incompatible) to 1.0 (perfect match)
        
        Scoring breakdown (when ELO included):
        - Task type match: 35%
        - Input compatibility: 15%
        - Output compatibility: 15%
        - Capability overlap: 7.5%
        - Tag similarity: 7.5%
        - ELO proximity: 30% (if ratings provided)
        """
        # Base ontology score (70% if ELO included, 100% otherwise)
        base_weight = 1.0 - elo_weight if (rating1 is not None and rating2 is not None) else 1.0
        score = 0.0
        max_score = 5.0
        
        # 1. Same task type (weight: 2.0)
        if ont1.task_type == ont2.task_type:
            score += 2.0
        
        # 2. Compatible input types (weight: 1.0)
        if ont1.input_schema.data_type == ont2.input_schema.data_type:
            score += 1.0
        
        # 3. Compatible output types (weight: 1.0)
        if ont1.output_schema.data_type == ont2.output_schema.data_type:
            score += 1.0
        
        # 4. Overlapping capabilities (weight: 0.5)
        if ont1.capabilities and ont2.capabilities:
            overlap = len(ont1.capabilities & ont2.capabilities)
            total = len(ont1.capabilities | ont2.capabilities)
            if total > 0:
                score += 0.5 * (overlap / total)
        
        # 5. Overlapping tags (weight: 0.5)
        if ont1.tags and ont2.tags:
            overlap = len(ont1.tags & ont2.tags)
            total = len(ont1.tags | ont2.tags)
            if total > 0:
                score += 0.5 * (overlap / total)
        
        ontology_score = (score / max_score) * base_weight
        
        # 6. ELO proximity - closer ratings = better match
        if rating1 is not None and rating2 is not None:
            # Calculate rating difference (max reasonable diff ~800 points)
            rating_diff = abs(rating1 - rating2)
            # Convert to similarity score (closer = higher)
            # Using exponential decay: e^(-diff/200)
            import math
            elo_similarity = math.exp(-rating_diff / 200)
            elo_score = elo_similarity * elo_weight
            
            return ontology_score + elo_score
        
        return ontology_score
    
    @staticmethod
    def find_compatible_models(
        target_ontology: ModelOntology,
        candidate_ontologies: List[ModelOntology],
        target_rating: Optional[float] = None,
        candidate_ratings: Optional[Dict[str, float]] = None,
        min_score: float = 0.5,
        elo_weight: float = 0.3,
        prefer_close_ratings: bool = True
    ) -> List[tuple[ModelOntology, float]]:
        """
        Find models compatible with target model
        
        Args:
            target_ontology: Target model's ontology
            candidate_ontologies: List of candidate model ontologies
            target_rating: Target model's ELO rating (optional)
            candidate_ratings: Dict mapping model_id to ELO rating (optional)
            min_score: Minimum compatibility score threshold
            elo_weight: Weight for ELO similarity (0.0-1.0)
            prefer_close_ratings: If True, prioritize models with similar ELO
        
        Returns:
            List of (ontology, score) tuples sorted by compatibility
        """
        results = []
        
        for candidate in candidate_ontologies:
            if candidate.model_id == target_ontology.model_id:
                continue
            
            # Get candidate rating if available
            cand_rating = None
            if candidate_ratings and candidate.model_id in candidate_ratings:
                cand_rating = candidate_ratings[candidate.model_id]
            
            score = OntologyMatcher.calculate_compatibility(
                target_ontology,
                candidate,
                rating1=target_rating,
                rating2=cand_rating,
                elo_weight=elo_weight if prefer_close_ratings else 0.0
            )
            
            if score >= min_score:
                results.append((candidate, score))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    @staticmethod
    def is_arena_compatible(
        model_ontologies: List[ModelOntology],
        strict: bool = True
    ) -> bool:
        """
        Check if models can compete in same arena
        
        Args:
            model_ontologies: List of model ontologies to check
            strict: If True, requires all models have same task type
        
        Returns:
            True if models can compete together
        """
        if len(model_ontologies) < 2:
            return False
        
        if strict:
            # All must have same task type
            task_types = {ont.task_type for ont in model_ontologies}
            if len(task_types) != 1:
                return False
        
        # All must have compatible I/O
        input_types = {ont.input_schema.data_type for ont in model_ontologies}
        output_types = {ont.output_schema.data_type for ont in model_ontologies}
        
        return len(input_types) == 1 and len(output_types) == 1


# Predefined ontology templates for common model types

def text_generation_ontology(
    model_id: str,
    max_length: int = 2048,
    **kwargs
) -> ModelOntology:
    """Template for text generation models"""
    return ModelOntology(
        model_id=model_id,
        task_type=TaskType.TEXT_GENERATION,
        input_schema=IOSchema(
            data_type=DataType.TEXT,
            description="Input text prompt",
            constraints={'max_length': max_length}
        ),
        output_schema=IOSchema(
            data_type=DataType.TEXT,
            description="Generated text",
            constraints={'max_length': max_length}
        ),
        capabilities={'generation', 'completion'},
        **kwargs
    )


def text_classification_ontology(
    model_id: str,
    num_classes: int,
    class_names: Optional[List[str]] = None,
    **kwargs
) -> ModelOntology:
    """Template for text classification models"""
    return ModelOntology(
        model_id=model_id,
        task_type=TaskType.TEXT_CLASSIFICATION,
        input_schema=IOSchema(
            data_type=DataType.TEXT,
            description="Input text to classify"
        ),
        output_schema=IOSchema(
            data_type=DataType.STRUCTURED,
            fields={
                'class': 'string',
                'score': 'float',
                'probabilities': 'array'
            },
            description="Classification result",
            constraints={
                'num_classes': num_classes,
                'class_names': class_names
            }
        ),
        capabilities={'classification', 'scoring'},
        **kwargs
    )


def question_answering_ontology(
    model_id: str,
    **kwargs
) -> ModelOntology:
    """Template for question-answering models"""
    return ModelOntology(
        model_id=model_id,
        task_type=TaskType.QUESTION_ANSWERING,
        input_schema=IOSchema(
            data_type=DataType.STRUCTURED,
            fields={
                'question': 'string',
                'context': 'string'
            },
            description="Question and context"
        ),
        output_schema=IOSchema(
            data_type=DataType.STRUCTURED,
            fields={
                'answer': 'string',
                'score': 'float',
                'start': 'int',
                'end': 'int'
            },
            description="Answer with confidence"
        ),
        capabilities={'qa', 'extraction'},
        **kwargs
    )
