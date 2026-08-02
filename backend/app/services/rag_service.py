import os
import re
import json
import httpx
import sqlite3
import zipfile
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
from app.services.llm_service import get_llm_provider, OllamaProvider, OpenAIProvider
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "lenny_vector_store.db")

class VectorStore:
    """A lightweight SQLite-based vector store for podcast transcript chunks."""
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                episode_id TEXT,
                episode_title TEXT,
                chunk_index INTEGER,
                content TEXT,
                embedding TEXT, -- JSON array of floats
                metadata TEXT   -- JSON dict of extra metadata
            )
        """)
        conn.commit()
        conn.close()

    def clear(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chunks")
        conn.commit()
        conn.close()

    def insert_chunk(self, chunk_id: str, episode_id: str, episode_title: str, chunk_index: int, content: str, embedding: List[float], metadata: Dict[str, Any]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO chunks (id, episode_id, episode_title, chunk_index, content, embedding, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (chunk_id, episode_id, episode_title, chunk_index, content, json.dumps(embedding), json.dumps(metadata))
        )
        conn.commit()
        conn.close()

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, episode_id, episode_title, chunk_index, content, embedding, metadata FROM chunks")
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for r in rows:
            result.append({
                "id": r["id"],
                "episode_id": r["episode_id"],
                "episode_title": r["episode_title"],
                "chunk_index": r["chunk_index"],
                "content": r["content"],
                "embedding": json.loads(r["embedding"]) if r["embedding"] else [],
                "metadata": json.loads(r["metadata"]) if r["metadata"] else {}
            })
        return result

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a*b for a, b in zip(v1, v2))
    norm_a = sum(a*a for a in v1) ** 0.5
    norm_b = sum(b*b for b in v2) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

class RAGService:
    _ollama_offline = False

    def __init__(self, vector_store: VectorStore = None):
        self.vector_store = vector_store or VectorStore()

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama, OpenAI, or a fallback representation if offline."""
        p_name = settings.LLM_PROVIDER.lower()
        
        if p_name == "openai" and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key-here":
            try:
                client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                resp = await client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return resp.data[0].embedding
            except Exception as e:
                logger.error(f"OpenAI embedding generation failed: {e}. Falling back to mock embeddings.")
        
        # Ollama embeddings (default local fallback)
        if not RAGService._ollama_offline and p_name == "ollama":
            # We try to use nomic-embed-text or the default model
            model = settings.OLLAMA_MODEL if hasattr(settings, "OLLAMA_MODEL") else "llama3"
            async with httpx.AsyncClient(timeout=1.0) as client:
                try:
                    resp = await client.post(
                        "http://localhost:11434/api/embeddings",
                        json={"model": model, "prompt": text}
                    )
                    if resp.status_code == 200:
                        return resp.json()["embedding"]
                except Exception as e:
                    logger.warning(f"Ollama embedding failed: {e}. Trying /api/embed...")
                    try:
                        resp = await client.post(
                            "http://localhost:11434/api/embed",
                            json={"model": model, "input": text}
                        )
                        if resp.status_code == 200:
                            return resp.json()["embeddings"][0]
                    except Exception as e2:
                        logger.error(f"Ollama alternate embedding failed: {e2}. Caching offline status.")
                        RAGService._ollama_offline = True

        # If both fail or we use Anthropic (no embedding API), let's create a stable deterministic mock vector
        # (hash-based) so RAG still runs/compiles and compiles cosine similarity gracefully.
        # 384 dimensions mock vector
        dims = 384
        vec = [0.0] * dims
        for char in text:
            idx = ord(char) % dims
            vec[idx] += 1.0
        # Normalize
        norm = sum(x*x for x in vec) ** 0.5
        if norm > 0:
            vec = [x/norm for x in vec]
        return vec

    def chunk_text(self, text: str, chunk_size: int = 1500, overlap: int = 300) -> List[str]:
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk_words = words[i:i+chunk_size]
            chunks.append(" ".join(chunk_words))
            if i + chunk_size >= len(words):
                break
            i += (chunk_size - overlap)
        return chunks

    async def ingest_transcripts_from_repo(self, repo_dir: str):
        """Processes md transcripts in the given folder and indexes them."""
        logger.info(f"Starting transcript ingestion from: {repo_dir}")
        self.vector_store.clear()
        
        md_files = []
        for root, dirs, files in os.walk(repo_dir):
            for file in files:
                if file.endswith(".md") and not file.lower() in ["readme.md", "contributing.md"]:
                    md_files.append(os.path.join(root, file))

        if not md_files:
            logger.warning(f"No Markdown files found in {repo_dir}")
            return

        for path in md_files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse frontmatter if present
                title = os.path.basename(path).replace(".md", "")
                episode_id = title.split("-")[0].strip()
                cleaned_content = content
                
                # Check for yaml frontmatter
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        frontmatter_str = parts[1]
                        cleaned_content = parts[2]
                        # parse title/episode from frontmatter if possible
                        for line in frontmatter_str.split("\n"):
                            if line.startswith("title:"):
                                title = line.split(":", 1)[1].strip().strip('"')
                            elif line.startswith("number:") or line.startswith("episode:"):
                                episode_id = line.split(":", 1)[1].strip().strip('"')

                chunks = self.chunk_text(cleaned_content)
                for idx, chunk in enumerate(chunks):
                    chunk_id = f"{episode_id}_{idx}"
                    embedding = await self.generate_embedding(chunk)
                    metadata = {
                        "filename": os.path.basename(path),
                        "episode_title": title,
                        "episode_id": episode_id
                    }
                    self.vector_store.insert_chunk(
                        chunk_id=chunk_id,
                        episode_id=episode_id,
                        episode_title=title,
                        chunk_index=idx,
                        content=chunk,
                        embedding=embedding,
                        metadata=metadata
                    )
                logger.info(f"Indexed episode: {title} ({len(chunks)} chunks)")
            except Exception as e:
                logger.error(f"Failed to ingest file {path}: {e}")

    async def download_and_ingest(self, target_dir: str = None):
        """Downloads the Zip file of Lenny's transcripts repo and ingests it."""
        if not target_dir:
            target_dir = os.path.join(os.path.dirname(DB_PATH), "transcripts_source")
        
        os.makedirs(target_dir, exist_ok=True)
        zip_path = os.path.join(target_dir, "transcripts.zip")
        
        logger.info("Downloading transcripts repo ZIP...")
        url = "https://github.com/ChatPRD/lennys-podcast-transcripts/archive/refs/heads/main.zip"
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise Exception(f"Failed to download transcripts repo ZIP: {resp.status_code}")
            with open(zip_path, "wb") as f:
                f.write(resp.content)

        logger.info("Extracting ZIP...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)

        # The extracted directory name is lennys-podcast-transcripts-main
        extracted_dir = os.path.join(target_dir, "lennys-podcast-transcripts-main")
        await self.ingest_transcripts_from_repo(extracted_dir)

    async def query(self, query_text: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Find the top_k most similar transcript chunks for a query."""
        query_embedding = await self.generate_embedding(query_text)
        all_chunks = self.vector_store.get_all_chunks()
        
        scored_chunks = []
        for chunk in all_chunks:
            sim = cosine_similarity(query_embedding, chunk["embedding"])
            scored_chunks.append((sim, chunk))
        
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        results = []
        for sim, chunk in scored_chunks[:top_k]:
            results.append({
                "score": sim,
                "content": chunk["content"],
                "episode_title": chunk["episode_title"],
                "episode_id": chunk["episode_id"],
                "metadata": chunk["metadata"]
            })
        return results
