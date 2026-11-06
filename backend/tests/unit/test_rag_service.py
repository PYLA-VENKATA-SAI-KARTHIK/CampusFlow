"""
Unit tests for CampusFlow RAG (Retrieval-Augmented Generation) Service.
Validates multi-domain retrieval, BM25 scoring, and grounded rubric evaluation
across all 7 uploaded question handbooks.
"""
import pytest
from app.core.rag.models import RAGDocument, RAGSearchResult, GroundedEvaluation
from app.core.rag.retriever import HybridRAGRetriever
from app.services.rag_service import RAGService


def test_rag_corpus_loaded():
    service = RAGService.get_instance()
    docs = service.retriever.documents
    assert len(docs) >= 900, f"Expected at least 900 documents, found {len(docs)}"
    
    # Verify categories present
    categories = {d.category for d in docs}
    assert "AI & Machine Learning" in categories
    assert "System Design" in categories
    assert "Full Stack & Web" in categories
    assert "Data Engineering" in categories
    assert "DevOps & Cloud Platform" in categories
    assert "HR & Behavioral" in categories


def test_devops_retrieval_and_source():
    service = RAGService.get_instance()
    query = "How do you troubleshoot a Kubernetes CrashLoopBackOff error?"
    response = service.search(query=query, track_id="role-devops", top_k=2)
    
    assert response.total_results > 0
    top_doc = response.results[0].document
    assert "CrashLoopBackOff" in top_doc.question
    assert "100 DevOps Engineer" in top_doc.source_document
    assert any(k.lower() in ["crashloopbackoff", "kubectl logs", "kubectl describe"] for k in top_doc.key_concepts)


def test_data_engineer_retrieval_and_source():
    service = RAGService.get_instance()
    query = "Explain Medallion Architecture Bronze Silver Gold"
    response = service.search(query=query, track_id="role-data", top_k=2)
    
    assert response.total_results > 0
    top_doc = response.results[0].document
    assert "Medallion Architecture" in top_doc.question
    assert "Azure Data Engineer" in top_doc.source_document
    assert "Bronze" in top_doc.answer
    assert "Silver" in top_doc.answer
    assert "Gold" in top_doc.answer


def test_aiml_grounded_evaluation():
    service = RAGService.get_instance()
    question = "Differentiate Between L1 And L2 Regularization?"
    
    # Candidate answer mentioning L1, L2, Lasso, Ridge
    good_answer = "L1 regularization is Lasso which adds absolute penalty driving weights to zero for sparsity, while L2 is Ridge which shrinks weights smoothly."
    eval_result = service.evaluate_answer_grounded(
        question_text=question,
        student_answer=good_answer,
        track_id="role-aiml",
    )
    
    assert isinstance(eval_result, GroundedEvaluation)
    assert eval_result.concept_coverage_score > 40.0
    assert len(eval_result.matched_concepts) >= 2
    assert "100 Machine Learning" in eval_result.source_document
    assert len(eval_result.reference_model_answer) > 20


def test_dynamic_track_questions_offset():
    service = RAGService.get_instance()
    q_batch_1 = service.get_track_questions("role-devops", count=5, offset=0)
    q_batch_2 = service.get_track_questions("role-devops", count=5, offset=5)
    
    assert len(q_batch_1) == 5
    assert len(q_batch_2) == 5
    ids_1 = {q.id for q in q_batch_1}
    ids_2 = {q.id for q in q_batch_2}
    
    # Batches should be completely distinct questions
    assert len(ids_1.intersection(ids_2)) == 0

