import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.router import AgentRouter
from app.agents.skills.qa_skill import QASkill
from app.agents.skills.essay_skill import EssaySkill
from app.agents.skills.artifact_skill import ArtifactSkill

@pytest.mark.anyio
async def test_router_routing_qa():
    router = AgentRouter()
    
    # Mock LLM classification returning "qa"
    mock_llm = AsyncMock()
    mock_llm.generate.side_effect = [
        "qa",                     # classification response
        "Grounded QA reply here."  # QASkill generate response
    ]
    
    # Mock RAG query returning mock chunks
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
    
    mock_llm = AsyncMock()
    mock_llm.generate.side_effect = [
        "essay",
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
    
    mock_llm = AsyncMock()
    mock_llm.generate.side_effect = [
        "artifact",
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
