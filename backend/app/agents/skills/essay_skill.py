"""EssaySkill — Ship30for30-style long-form essay generation.

Demo-optimisation notes
-----------------------
* ``num_predict=1800``: Caps generation at ~1300 words — sufficient for a
  comprehensive Ship30for30 essay without letting the model meander.
* No conversation history: Essays are always standalone creative outputs.
  Passing prior chat turns wastes tokens and doesn't improve quality.
* ``top_k=5`` retained: More transcript context produces richer essays.
"""

import time
import logging
from typing import List, Dict, Any

from app.agents.skills.base import BaseSkill
from app.services.rag_service import RAGService
from app.services.llm_service import get_llm_provider
from app.core.config import settings

logger = logging.getLogger(__name__)

# Per-chunk character cap (same formula as QASkill)
_CHUNK_CHAR_LIMIT = settings.RAG_CHUNK_WORD_LIMIT * 5


def _truncate_chunk(text: str, max_chars: int = _CHUNK_CHAR_LIMIT) -> str:
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars // 2:
        truncated = truncated[:last_space]
    return truncated + " […]"


class EssaySkill(BaseSkill):
    @property
    def name(self) -> str:
        return "essay"

    @property
    def description(self) -> str:
        return "Generate a long-form (~1250 words) Ship30for30-style essay based on Lenny's Podcast knowledge."

    async def execute(self, prompt: str, context: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        rag = RAGService()
        # Keep top_k=5 for richer essay context
        chunks = await rag.query(prompt, top_k=5)

        logger.info(
            "[Essay] Retrieved %d RAG chunks for query: %r",
            len(chunks),
            prompt[:80],
        )

        context_str = ""
        sources = []
        total_context_chars = 0
        for idx, c in enumerate(chunks):
            source_info = f"Episode: {c['episode_title']} (ID: {c['episode_id']})"
            chunk_text = _truncate_chunk(c["content"])
            context_str += f"--- Excerpt {idx + 1} ({source_info}) ---\n{chunk_text}\n\n"
            total_context_chars += len(chunk_text)
            sources.append({
                "episode_title": c["episode_title"],
                "episode_id": c["episode_id"],
            })

        logger.info(
            "[Essay] RAG context assembled | chunks=%d | total_context_chars≈%d",
            len(chunks),
            total_context_chars,
        )

        system_prompt = (
            "You are a world-class creator specializing in writing Ship30for30-style essays. "
            "Your goal is to synthesize the transcript excerpts provided below into a deep, "
            "engaging, and highly skimmable essay of approximately 1250 words.\n\n"
            "Strict Writing Guidelines:\n"
            "1. Hook: Start with a strong, single-sentence opening hook that commands attention.\n"
            "2. Structure: Break the article down into clear sections with descriptive headers.\n"
            "3. Skimmability: Use short paragraphs (1-3 sentences maximum). "
            "Bold important terms, concepts, and ideas. Use bullet points for lists and comparisons.\n"
            "4. Grounded in Evidence: Use only facts, quotes, and insights mentioned in the "
            "provided transcripts. Do not fabricate quotes or pretend Lenny said something "
            "not in the source text.\n"
            "5. Takeaways: End with a clear, bold, actionable takeaway for product managers "
            "or growth operators.\n\n"
            f"Here are the transcript passages to synthesize:\n{context_str}"
        )

        # Essays are standalone — no conversation history needed
        messages = [
            {"role": "user", "content": f"Write a comprehensive Ship30for30-style essay on the topic: {prompt}"}
        ]

        llm = get_llm_provider(provider_name=kwargs.get("provider"))
        start_time = time.monotonic()
        response_text = await llm.generate(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=1700,
            options={"num_predict": 1700},  # ~1250 words — right size for a Ship30for30 essay
        )

        elapsed = time.monotonic() - start_time
        logger.info("[Essay] LLM generation completed in %.1fs", elapsed)

        unique_sources = list({s["episode_id"]: s for s in sources}.values())
        source_footnotes = "\n\n**Sources:**\n" + "\n".join(
            f"- {s['episode_title']} (Episode {s['episode_id']})" for s in unique_sources
        )

        return {
            "content": response_text + source_footnotes,
            "sources": sources,
        }
