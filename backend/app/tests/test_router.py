"""Tests for AgentRouter — verifies routing logic for qa, essay, and artifact skills.

Updated for keyword-first routing:
- Essay and artifact prompts that match keyword patterns bypass the LLM classifier.
  Their mock_llm.generate side_effect list only needs ONE entry (the skill response).
- QA prompts that don't match keywords still use the LLM classifier, so their
  side_effect list needs TWO entries (classification + skill response).
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.router import AgentRouter, _keyword_classify
from app.agents.skills.qa_skill import QASkill
from app.agents.skills.essay_skill import EssaySkill
from app.agents.skills.artifact_skill import ArtifactSkill


# ---------------------------------------------------------------------------
# Unit tests for the keyword classifier
# ---------------------------------------------------------------------------

def test_keyword_classify_essay_ship30for30():
    assert _keyword_classify("Write a Ship30for30-style essay on metrics") == "essay"

def test_keyword_classify_essay_explicit():
    assert _keyword_classify("Write an essay on product-market fit") == "essay"

def test_keyword_classify_artifact_html():
    assert _keyword_classify("Create an HTML growth experiment dashboard template with CSS styling.") == "artifact"

def test_keyword_classify_artifact_template():
    assert _keyword_classify("Generate a roadmap template for my team") == "artifact"

def test_keyword_classify_qa_returns_none():
    # QA prompts should NOT match — returns None so LLM fallback is used
    assert _keyword_classify("What does Lenny say about finding product-market fit?") is None
    assert _keyword_classify("How should a startup think about growth?") is None


# ---------------------------------------------------------------------------
# Integration tests for router routing
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_router_routing_qa():
    router = AgentRouter()

    # QA prompt → no keyword match → LLM classifier fires → two generate calls
    mock_llm = AsyncMock()
    mock_llm.generate.side_effect = [
        "qa",                      # classification response
        "Grounded QA reply here."  # QASkill generate response
    ]

    mock_rag_query = AsyncMock(return_value=[{
        "score": 0.9,
        "content": "This is transcript text about growth.",
        "episode_title": "Ada Chen",
        "episode_id": "1",
        "metadata": {}
    }])

    with patch("app.agents.router.get_llm_provider", return_value=mock_llm), \
         patch("app.agents.skills.qa_skill.get_llm_provider", return_value=mock_llm), \
         patch("app.services.rag_service.RAGService.query", new=mock_rag_query):

        result = await router.route_and_execute("What does Ada Chen say about product management?", [])
        assert result["skill_used"] == "qa"
        assert "Grounded QA reply here." in result["content"]
        assert "Sources:" in result["content"]


@pytest.mark.anyio
async def test_router_routing_essay():
    router = AgentRouter()

    # Essay prompt matches keyword fast-path → LLM classifier NOT called →
    # mock_llm only needs one side_effect entry (the skill response itself).
    mock_llm = AsyncMock()
    mock_llm.generate.side_effect = [
        "Here is a 1250-word Ship30for30-style essay about growth hacking."
    ]

    mock_rag_query = AsyncMock(return_value=[{
        "score": 0.8,
        "content": "Growth hacking excerpts.",
        "episode_title": "Growth Pod",
        "episode_id": "2",
        "metadata": {}
    }])

    with patch("app.agents.router.get_llm_provider", return_value=mock_llm), \
         patch("app.agents.skills.essay_skill.get_llm_provider", return_value=mock_llm), \
         patch("app.services.rag_service.RAGService.query", new=mock_rag_query):

        result = await router.route_and_execute("Write an essay on growth hacking", [])
        assert result["skill_used"] == "essay"
        assert "Here is a 1250-word" in result["content"]
        assert "Sources:" in result["content"]


@pytest.mark.anyio
async def test_router_routing_artifact():
    router = AgentRouter()

    # Artifact prompt matches keyword fast-path → LLM classifier NOT called.
    mock_llm = AsyncMock()
    mock_llm.generate.side_effect = [
        'Sure! Here is a roadmap dashboard:<artifact title="Roadmap Page" type="code"><html><body>Roadmap content</body></html></artifact>'
    ]

    mock_rag_query = AsyncMock(return_value=[{
        "score": 0.8,
        "content": "Roadmap notes.",
        "episode_title": "Roadmap Pod",
        "episode_id": "3",
        "metadata": {}
    }])

    with patch("app.agents.router.get_llm_provider", return_value=mock_llm), \
         patch("app.agents.skills.artifact_skill.get_llm_provider", return_value=mock_llm), \
         patch("app.services.rag_service.RAGService.query", new=mock_rag_query):

        result = await router.route_and_execute("Generate a dashboard page for my roadmap", [])
        assert result["skill_used"] == "artifact"
        assert "artifact" in result
        assert result["artifact"]["title"] == "Roadmap Page"
        assert result["artifact"]["artifact_type"] == "code"
        assert "Roadmap content" in result["artifact"]["content"]
