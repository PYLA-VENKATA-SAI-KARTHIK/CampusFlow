"""
CampusFlow — RAG System Data Models & Schemas.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class RAGDocument(BaseModel):
    id: str = Field(..., description="Unique document ID (e.g. devops-42, aiml-12)")
    track_id: str = Field(..., description="Target interview track ID (e.g. role-devops, role-aiml)")
    category: str = Field(..., description="High-level category (e.g. DevOps & Cloud Platform)")
    subtopic: str = Field(..., description="Specific subtopic (e.g. Kubernetes, Delta Lake)")
    question: str = Field(..., description="Standardized interview question")
    answer: str = Field(..., description="Canonical model answer extracted from official handbooks")
    key_concepts: List[str] = Field(default_factory=list, description="Core keywords & technical concepts required")
    difficulty: str = Field("INTERMEDIATE", description="FOUNDATIONAL, INTERMEDIATE, or ADVANCED")
    source_document: str = Field(..., description="Origin handbook/PDF title")


class RAGSearchResult(BaseModel):
    document: RAGDocument
    score: float = Field(..., description="Relevance similarity score (0.0 to 1.0)")
    matched_terms: List[str] = Field(default_factory=list, description="Search query terms matched in document")


class RAGQueryRequest(BaseModel):
    query: str = Field(..., description="Query string or candidate transcript to ground")
    track_id: Optional[str] = Field(None, description="Optional track filter")
    top_k: int = Field(3, ge=1, le=10, description="Number of results to retrieve")


class RAGQueryResponse(BaseModel):
    query: str
    track_id: Optional[str] = None
    total_results: int
    results: List[RAGSearchResult]


class GroundedEvaluation(BaseModel):
    concept_coverage_score: float = Field(..., description="Score 0-100 indicating percentage of key concepts covered")
    matched_concepts: List[str] = Field(default_factory=list, description="Key concepts detected in candidate answer")
    missing_concepts: List[str] = Field(default_factory=list, description="Key concepts the candidate missed")
    reference_model_answer: str = Field(..., description="Official textbook answer from the PDF handbook")
    source_document: str = Field(..., description="Source PDF handbook citation")
    rubric_guidance: str = Field(..., description="Targeted guidance derived from the official handbook")

