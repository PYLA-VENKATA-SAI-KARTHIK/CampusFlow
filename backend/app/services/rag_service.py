"""
CampusFlow — RAG (Retrieval-Augmented Generation) Service.

Provides category-grounded retrieval, question curation, and factual evaluation
against the verified 7 interview question PDF handbooks.
"""
from __future__ import annotations

import os
import re
from typing import List, Optional

from app.core.rag.models import (
    GroundedEvaluation,
    RAGDocument,
    RAGQueryResponse,
    RAGSearchResult,
)
from app.core.rag.retriever import HybridRAGRetriever, tokenize


class RAGService:
    _instance: Optional[RAGService] = None

    def __init__(self, data_path: Optional[str] = None) -> None:
        if data_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "core", "rag", "knowledge_data.json")
        self.retriever = HybridRAGRetriever(data_path=data_path)

    @classmethod
    def get_instance(cls) -> RAGService:
        if cls._instance is None:
            cls._instance = RAGService()
        return cls._instance

    def search(
        self, query: str, track_id: Optional[str] = None, top_k: int = 3
    ) -> RAGQueryResponse:
        results = self.retriever.retrieve(query=query, track_id=track_id, top_k=top_k)
        return RAGQueryResponse(
            query=query,
            track_id=track_id,
            total_results=len(results),
            results=results,
        )

    def get_track_questions(
        self, track_id: str, count: int = 5, offset: int = 0
    ) -> List[RAGDocument]:
        return self.retriever.get_track_questions(track_id=track_id, count=count, offset=offset)

    def evaluate_answer_grounded(
        self,
        question_text: str,
        student_answer: str,
        track_id: str,
        expected_keywords: Optional[List[str]] = None,
    ) -> GroundedEvaluation:
        # Retrieve the canonical document matching this question
        search_results = self.retriever.retrieve(
            query=question_text, track_id=track_id, top_k=1
        )

        if search_results:
            ref_doc = search_results[0].document
            source_doc = ref_doc.source_document
            ref_answer = ref_doc.answer
            target_concepts = list(ref_doc.key_concepts)
        else:
            # Fallback to general guidance if query wasn't matched
            source_doc = "CampusFlow Curated Engineering Standards"
            ref_answer = "Provide a structured, step-by-step technical explanation covering architectural trade-offs, edge cases, and concrete production patterns."
            target_concepts = expected_keywords or ["scalability", "trade-offs", "best practices"]

        # Merge with expected keywords from request
        if expected_keywords:
            for kw in expected_keywords:
                if kw.lower() not in [c.lower() for c in target_concepts]:
                    target_concepts.append(kw)

        # Deduplicate target concepts case-insensitively and filter short tokens
        unique_targets: List[str] = []
        seen_targets = set()
        for c in target_concepts:
            c_clean = c.strip()
            c_low = c_clean.lower()
            if c_low not in seen_targets and len(c_clean) >= 2:
                seen_targets.add(c_low)
                unique_targets.append(c_clean)

        student_lower = student_answer.lower()
        matched: List[str] = []
        missing: List[str] = []

        for concept in unique_targets:
            clean_concept = concept.strip()
            # Check for substring or boundary match
            escaped = re.escape(clean_concept.lower())
            if re.search(r"\b" + escaped + r"\b", student_lower) or clean_concept.lower() in student_lower:
                matched.append(clean_concept)
            else:
                missing.append(clean_concept)

        total_concepts = max(1, len(unique_targets))
        coverage_score = round((len(matched) / total_concepts) * 100.0, 1)

        # Build rubric guidance grounded in the PDF handbook
        if missing:
            guidance = (
                f"Grounded in '{source_doc}': To achieve full technical precision, articulate the following missing concepts: "
                f"{', '.join(missing[:4])}. For example: {ref_answer[:160]}..."
            )
        else:
            guidance = (
                f"Grounded in '{source_doc}': Excellent technical coverage! Your response successfully incorporated all essential domain criteria."
            )

        return GroundedEvaluation(
            concept_coverage_score=coverage_score,
            matched_concepts=matched,
            missing_concepts=missing,
            reference_model_answer=ref_answer,
            source_document=source_doc,
            rubric_guidance=guidance,
        )

