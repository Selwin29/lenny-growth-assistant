import time
import logging
from typing import List, Dict, Any

from app.agents.skills.base import BaseSkill
from app.services.rag_service import RAGService
from app.services.llm_service import get_llm_provider
from app.core.config import settings

logger = logging.getLogger(__name__)

# Maximum characters per RAG chunk included in the LLM system prompt.
# Derived from RAG_CHUNK_WORD_LIMIT (words * ~5 chars/word).
_CHUNK_CHAR_LIMIT = settings.RAG_CHUNK_WORD_LIMIT * 5


def _truncate_chunk(text: str, max_chars: int = _CHUNK_CHAR_LIMIT) -> str:
    """Truncate a chunk to `max_chars`, appending '…' when cut."""
    if len(text) <= max_chars:
        return text
    # Cut at last whitespace boundary within limit
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars // 2:
        truncated = truncated[:last_space]
    return truncated + " […]"


class QASkill(BaseSkill):
    @property
    def name(self) -> str:
        return "qa"

    @property
    def description(self) -> str:
        return "Answer product management or growth questions strictly based on Lenny's Podcast transcripts."

    async def execute(self, prompt: str, context: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        rag = RAGService()
        # Retrieve context chunks
        chunks = await rag.query(prompt, top_k=4)

        logger.info(
            "[QA] Retrieved %d RAG chunks for query: %r",
            len(chunks),
            prompt[:80],
        )

        if not chunks or all(c["score"] < 0.15 for c in chunks):
            return {
                "content": (
                    "I couldn't find enough evidence in Lenny's podcast transcripts to answer "
                    "that question. Could you try asking about a different product or growth topic?"
                ),
                "sources": [],
            }

        # Build context string — truncate each chunk to limit prompt size
        context_str = ""
        sources = []
        total_context_chars = 0
        for idx, c in enumerate(chunks):
            source_info = f"Episode: {c['episode_title']} (ID: {c['episode_id']})"
            chunk_text = _truncate_chunk(c["content"])
            context_str += f"--- Source {idx + 1}: {source_info} ---\n{chunk_text}\n\n"
            total_context_chars += len(chunk_text)
            sources.append({
                "episode_title": c["episode_title"],
                "episode_id": c["episode_id"],
            })

        logger.info(
            "[QA] RAG context assembled | chunks=%d | total_context_chars≈%d (~%d words)",
            len(chunks),
            total_context_chars,
            total_context_chars // 5,
        )

        system_prompt = (
            "You are the Lenny Growth Assistant. You answer questions about product management, growth, strategy, "
            "and startups STRICTLY based on the transcript excerpts provided below. Do not invent details or use external knowledge. "
            "If the transcripts do not contain enough information to answer the user's question, state clearly that you do not "
            "have enough evidence in the transcripts. Reference the episode titles/IDs in your answers to credit the sources.\n\n"
            f"Here are the relevant transcript passages:\n{context_str}"
        )

        # Build message chain — limit conversation history to last 4 turns
        messages = []
        for msg in context[-4:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})

        llm = get_llm_provider()
        start_time = time.monotonic()
        response_text = await llm.generate(messages=messages, system_prompt=system_prompt)
        elapsed = time.monotonic() - start_time

        logger.info("[QA] LLM generation completed in %.1fs", elapsed)

        # Deduplicated source footnotes
        unique_sources = list({s["episode_id"]: s for s in sources}.values())
        source_footnotes = "\n\n**Sources:**\n" + "\n".join(
            f"- {s['episode_title']} (Episode {s['episode_id']})" for s in unique_sources
        )

        return {
            "content": response_text + source_footnotes,
            "sources": sources,
        }
