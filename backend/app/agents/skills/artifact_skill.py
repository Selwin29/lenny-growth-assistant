import re
import time
import logging
from typing import List, Dict, Any

from app.agents.skills.base import BaseSkill
from app.services.rag_service import RAGService
from app.services.llm_service import get_llm_provider
from app.core.config import settings

logger = logging.getLogger(__name__)

_CHUNK_CHAR_LIMIT = settings.RAG_CHUNK_WORD_LIMIT * 5


def _truncate_chunk(text: str, max_chars: int = _CHUNK_CHAR_LIMIT) -> str:
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars // 2:
        truncated = truncated[:last_space]
    return truncated + " […]"

class ArtifactSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "artifact"

    @property
    def description(self) -> str:
        return "Generate structured documents, code snippets, or UI components (HTML/CSS, Markdown) stored as artifacts."

    async def execute(self, prompt: str, context: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        rag = RAGService()
        chunks = await rag.query(prompt, top_k=4)

        logger.info(
            "[Artifact] Retrieved %d RAG chunks for query: %r",
            len(chunks),
            prompt[:80],
        )

        context_str = ""
        total_context_chars = 0
        for idx, c in enumerate(chunks):
            chunk_text = _truncate_chunk(c["content"])
            context_str += f"--- Excerpt {idx + 1} ({c['episode_title']}) ---\n{chunk_text}\n\n"
            total_context_chars += len(chunk_text)

        logger.info(
            "[Artifact] RAG context assembled | chunks=%d | total_context_chars≈%d",
            len(chunks),
            total_context_chars,
        )

        system_prompt = (
            "You are an expert design and technical assistant. The user wants you to generate a document, template, UI component, or tool.\n"
            "You must output two things in your response:\n"
            "1. A short, helpful intro message to show in the chat.\n"
            "2. The artifact content wrapped in specific XML-like tags so it can be extracted programmatically:\n"
            "   Use <artifact title=\"[Title]\" type=\"[markdown|code]\">[artifact content]</artifact>.\n\n"
            "Types of Artifacts:\n"
            "- markdown: Use for documents, guides, lists, and templates.\n"
            "- code: Use for full, self-contained HTML/CSS files that render a web preview. Do not write markdown inside a code/HTML artifact.\n\n"
            "For HTML/CSS artifacts:\n"
            "- Write modern, complete HTML with Tailwind or beautiful embedded vanilla CSS styles (e.g., inside <style> tags).\n"
            "- Ensure it looks professional, modern, responsive, and functional (interactive with script tags if appropriate).\n\n"
            f"Ground your generation in Lenny's Podcast insights:\n{context_str}"
        )

        messages = [
            {"role": "user", "content": f"Generate an artifact for: {prompt}"}
        ]

        llm = get_llm_provider()
        start_time = time.monotonic()
        response_text = await llm.generate(messages=messages, system_prompt=system_prompt)
        elapsed = time.monotonic() - start_time
        logger.info("[Artifact] LLM generation completed in %.1fs", elapsed)

        # Parse tags using regex
        pattern = r'<artifact\s+title="([^"]+)"\s+type="([^"]+)"\s*>(.*?)</artifact>'
        match = re.search(pattern, response_text, re.DOTALL)

        if match:
            title = match.group(1)
            artifact_type = match.group(2)
            artifact_content = match.group(3).strip()
            # Clean response text to extract the chat message content (remove the artifact tag from chat text)
            chat_text = re.sub(pattern, f"\n*(Artifact **{title}** has been generated and is visible in the side panel)*", response_text, flags=re.DOTALL).strip()
            
            return {
                "content": chat_text,
                "artifact": {
                    "title": title,
                    "artifact_type": artifact_type,
                    "content": artifact_content
                }
            }
        else:
            # Fallback if AI forgot formatting tags
            return {
                "content": response_text,
                "artifact": {
                    "title": "Generated Artifact",
                    "artifact_type": "markdown",
                    "content": response_text
                }
            }
        
        return {"content": response_text}
