"""QASkill — grounded question answering from Lenny's podcast transcripts.

Demo-optimisation notes (applied without removing functionality)
---------------------------------------------------------------
* ``top_k=3``     : Retrieve 3 chunks instead of 4 — smaller RAG context,
                    slightly faster embedding similarity scan.
* ``context[-2:]``: Pass only the single most recent exchange (user + assistant)
                    as conversation history.  A demo's first question needs zero
                    history; multi-turn benefit is marginal vs. the token cost.
* ``num_predict=600``: Caps Ollama token generation at ~450 words.  Enough for
                    3–6 well-developed bullet points with source attribution.
* System prompt wording: Explicitly instructs the model to respond concisely
                    with 3–6 key points so it doesn't meander.
"""

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
        # Retrieve top-3 most relevant chunks (down from 4 — keeps prompt tighter)
        chunks = await rag.query(prompt, top_k=3)

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
            "You are the Lenny Growth Assistant. Answer questions about product management, "
            "growth, and startups STRICTLY based on the transcript excerpts provided below.\n\n"
            "CRITICAL SPEAKER ATTRIBUTION RULES:\n"
            "1. Distinguish between LENNY RACHITSKY (the podcast host) and PODCAST GUESTS (the interviewees featured in each episode).\n"
            "2. If the user asks what LENNY says about a topic, check if the excerpts contain direct statements from Lenny himself. "
            "If the evidence comes from podcast guests rather than Lenny, start your response by explicitly stating:\n"
            '   "The available transcripts don\'t contain a direct statement from Lenny on this specific question. However, related podcast guests discuss this topic in these ways:"\n'
            "   Do NOT phrase advice or quotes from guests as something Lenny personally said.\n"
            "3. Clearly identify WHO stated each insight (e.g., name the specific guest or Lenny) along with the episode title/ID.\n"
            "4. If the provided transcripts do NOT contain relevant information on the topic (e.g. quantum computing or unrelated topics), "
            "state clearly that the available transcripts do not contain sufficient evidence to answer the question. Do NOT fabricate information, guests, or citations.\n\n"
            "RESPONSE FORMAT:\n"
            "- Provide a clear, structured answer with 3 to 6 concise bullet points (1–2 sentences each).\n"
            "- Bold key terms, speaker names, and core concepts.\n"
            "- Include exact episode citations.\n\n"
            f"Relevant transcript passages:\n{context_str}"
        )


        # Build message chain — limit to last 1 exchange (2 messages) to keep prompt small
        messages = []
        for msg in context[-2:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})

        llm = get_llm_provider(provider_name=kwargs.get("provider"))
        start_time = time.monotonic()
        response_text = await llm.generate(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=600,
            options={"num_predict": 600},  # ~450 words — enough for 3–6 quality bullets
        )

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
