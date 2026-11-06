"""
CampusFlow — Hybrid BM25/TF-IDF RAG Retriever Engine.

Provides ultra-fast, deterministic in-memory retrieval across the 996+ interview questions
extracted from the official industry handbooks and PDFs.
"""
from __future__ import annotations

import json
import math
import os
import re
from typing import Dict, List, Optional, Set, Tuple

from app.core.rag.models import RAGDocument, RAGSearchResult

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
    "by", "can", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for",
    "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once",
    "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}


def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text to lowercase alphanumeric tokens, stripping stopwords."""
    raw_tokens = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())
    return [t for t in raw_tokens if t not in STOPWORDS]


class HybridRAGRetriever:
    def __init__(self, data_path: Optional[str] = None) -> None:
        if data_path is None:
            # Default to adjacent knowledge_data.json
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(current_dir, "knowledge_data.json")

        self.data_path = data_path
        self.documents: List[RAGDocument] = []
        self.doc_tokens: List[List[str]] = []
        self.inverted_index: Dict[str, List[int]] = {}  # term -> list of doc indices
        self.idf: Dict[str, float] = {}
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0

        # BM25 Hyperparameters
        self.k1 = 1.5
        self.b = 0.75

        self._load_corpus()

    def _load_corpus(self) -> None:
        if not os.path.exists(self.data_path):
            return

        with open(self.data_path, "r", encoding="utf-8") as f:
            raw_items = json.load(f)

        self.documents = [RAGDocument(**item) for item in raw_items]
        n_docs = len(self.documents)
        if n_docs == 0:
            return

        total_length = 0
        df: Dict[str, int] = {}  # Document frequency of term

        for doc_idx, doc in enumerate(self.documents):
            # Rich combined text representation: question + key concepts (boosted) + answer
            boosted_concepts = " ".join(doc.key_concepts * 3)
            doc_text = f"{doc.question} {doc.question} {boosted_concepts} {doc.answer}"
            tokens = tokenize(doc_text)
            self.doc_tokens.append(tokens)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_length += doc_len

            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.inverted_index.setdefault(t, []).append(doc_idx)
                df[t] = df.get(t, 0) + 1

        self.avg_doc_len = total_length / max(1, n_docs)

        # Precompute IDF for all terms
        for term, freq in df.items():
            # Standard Lucene/BM25 IDF formula
            self.idf[term] = math.log(1.0 + (n_docs - freq + 0.5) / (freq + 0.5))

    def retrieve(
        self,
        query: str,
        track_id: Optional[str] = None,
        top_k: int = 3,
        threshold: float = 0.05,
    ) -> List[RAGSearchResult]:
        """
        Retrieves top_k relevant documents for the query using BM25 scoring with exact phrase boost.
        """
        query_tokens = tokenize(query)
        if not query_tokens or not self.documents:
            return []

        # Candidate doc indices matching at least one token
        candidate_indices: Set[int] = set()
        for t in query_tokens:
            if t in self.inverted_index:
                candidate_indices.update(self.inverted_index[t])

        if not candidate_indices:
            # Fallback to general track docs if filter supplied
            if track_id:
                track_docs = [
                    (i, doc) for i, doc in enumerate(self.documents) if doc.track_id == track_id
                ]
                return [
                    RAGSearchResult(document=doc, score=0.5, matched_terms=[])
                    for i, doc in track_docs[:top_k]
                ]
            return []

        clean_lower_query = query.lower()
        scored_candidates: List[Tuple[int, float, List[str]]] = []

        for doc_idx in candidate_indices:
            doc = self.documents[doc_idx]
            # Track filter check
            if track_id and doc.track_id != track_id:
                continue

            doc_tokens = self.doc_tokens[doc_idx]
            doc_len = self.doc_lengths[doc_idx]

            # Count term frequencies in this doc
            tf_map: Dict[str, int] = {}
            for t in doc_tokens:
                if t in query_tokens:
                    tf_map[t] = tf_map.get(t, 0) + 1

            matched_terms = list(tf_map.keys())
            if not matched_terms:
                continue

            # Compute BM25 score
            bm25_score = 0.0
            for t, count in tf_map.items():
                idf_val = self.idf.get(t, 0.1)
                numerator = count * (self.k1 + 1.0)
                denominator = count + self.k1 * (1.0 - self.b + self.b * (doc_len / max(1.0, self.avg_doc_len)))
                bm25_score += idf_val * (numerator / max(0.001, denominator))

            # Phrase boost: if query phrase occurs in question or answer
            if clean_lower_query in doc.question.lower():
                bm25_score *= 2.0
            elif any(concept.lower() in clean_lower_query for concept in doc.key_concepts):
                bm25_score *= 1.4

            scored_candidates.append((doc_idx, bm25_score, matched_terms))

        if not scored_candidates:
            return []

        # Normalize score to 0.0 - 1.0 range
        max_score = max(score for _, score, _ in scored_candidates)
        results: List[RAGSearchResult] = []

        # Sort descending
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        for doc_idx, score, matched in scored_candidates[:top_k]:
            normalized_score = round(min(1.0, score / max(1.0, max_score)), 3)
            if normalized_score >= threshold:
                results.append(
                    RAGSearchResult(
                        document=self.documents[doc_idx],
                        score=normalized_score,
                        matched_terms=matched,
                    )
                )

        return results

    def get_track_questions(
        self, track_id: str, count: int = 5, offset: int = 0
    ) -> List[RAGDocument]:
        """Returns non-repeating questions for a track with optional offset for question refresh."""
        filtered = [doc for doc in self.documents if doc.track_id == track_id]
        if not filtered:
            return []
        
        start = offset % len(filtered)
        # Wrap around slice
        sliced = filtered[start : start + count]
        if len(sliced) < count:
            sliced += filtered[: count - len(sliced)]
        return sliced

