import pytest
import os
import tempfile
import sqlite3
from app.services.rag_service import RAGService, VectorStore, cosine_similarity

def test_cosine_similarity():
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)
    assert cosine_similarity([1, 1], [1, 1]) == pytest.approx(1.0)
    assert cosine_similarity([1, 2, 3], [4, 5, 6]) > 0.9  # close vectors

def test_chunking():
    rag = RAGService()
    text = "hello " * 2000
    chunks = rag.chunk_text(text, chunk_size=1000, overlap=200)
    assert len(chunks) > 1
    assert all(len(c.split()) <= 1000 for c in chunks)

@pytest.mark.anyio
async def test_vector_store():
    # Use temporary file for test db
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
        
    try:
        store = VectorStore(db_path=db_path)
        # Verify it creates tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chunks'")
        assert cursor.fetchone() is not None
        conn.close()

        # Test insert and query
        rag = RAGService(vector_store=store)
        store.insert_chunk(
            chunk_id="ep1_0",
            episode_id="ep1",
            episode_title="Episode 1",
            chunk_index=0,
            content="This is a podcast about growth hacking and conversion optimization.",
            embedding=[1.0, 0.0, 0.0],
            metadata={"source": "test"}
        )
        
        store.insert_chunk(
            chunk_id="ep2_0",
            episode_id="ep2",
            episode_title="Episode 2",
            chunk_index=0,
            content="This is a podcast about hiring product managers and engineering leaders.",
            embedding=[0.0, 1.0, 0.0],
            metadata={"source": "test"}
        )

        # Mock the embedding method to return test vectors
        async def mock_embed(text):
            if "growth" in text:
                return [1.0, 0.0, 0.0]
            else:
                return [0.0, 1.0, 0.0]

        rag.generate_embedding = mock_embed

        results = await rag.query("growth optimization", top_k=1)
        assert len(results) == 1
        assert results[0]["episode_title"] == "Episode 1"
        assert "growth hacking" in results[0]["content"]

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
