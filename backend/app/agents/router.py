"""AgentRouter — classifies the user's intent and dispatches to the correct skill.

Classification strategy (fastest first)
-----------------------------------------
1. Keyword/regex fast-path: handles obvious essay and artifact requests without
   calling Ollama.  Covers the most common demo prompts in O(1) time.
2. LLM fallback: reserved for genuinely ambiguous requests that the keyword
   heuristic cannot confidently classify.

Skill routing
-------------
- ``qa``       : Grounded question answering from Lenny's podcast transcripts.
- ``essay``    : Ship30for30-style long-form essay generation.
- ``artifact`` : HTML/CSS, Markdown templates, code files — rendered in-app.
"""

import re
import logging
from typing import List, Dict, Any, Optional

from app.agents.skills.qa_skill import QASkill
from app.agents.skills.essay_skill import EssaySkill
from app.agents.skills.artifact_skill import ArtifactSkill
from app.services.llm_service import get_llm_provider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keyword patterns for fast-path classification
# ---------------------------------------------------------------------------

# Essay signals: explicit essay/article/newsletter request words, OR Ship30for30
_ESSAY_PATTERNS = re.compile(
    r"\b("
    r"ship\s*30\s*for\s*30"
    r"|essay"
    r"|write\s+(?:a\s+)?(?:long[-\s]?form\s+)?article"
    r"|write\s+(?:a\s+)?newsletter"
    r"|write\s+(?:a\s+)?blog\s+post"
    r"|write\s+(?:a\s+)?write[-\s]?up"
    r"|write\s+(?:a\s+)?piece\s+on"
    r")\b",
    re.IGNORECASE,
)

# Artifact signals: requests for HTML/CSS/code files, templates, dashboards,
# UI components, spreadsheets, roadmaps, visual pages, or previews.
_ARTIFACT_PATTERNS = re.compile(
    r"\b("
    r"html"
    r"|css"
    r"|template"
    r"|dashboard"
    r"|component"
    r"|spreadsheet"
    r"|roadmap"
    r"|mock(?:up)?"
    r"|landing\s+page"
    r"|web\s+page"
    r"|code\s+(?:file|snippet)"
    r"|generate\s+(?:a\s+)?(?:html|css|code|file)"
    r"|create\s+(?:a\s+)?(?:html|css|code|file|template|dashboard)"
    r"|build\s+(?:a\s+)?(?:html|css|page|template|dashboard)"
    r")\b",
    re.IGNORECASE,
)


def _keyword_classify(prompt: str) -> Optional[str]:
    """Return a skill name if the prompt clearly matches a pattern, else None.

    Returns
    -------
    ``"essay"``, ``"artifact"``, or ``None`` (ambiguous → fall through to LLM).
    QA is the default fallback — it never needs a keyword match.
    """
    # Essay is checked before artifact so "write an essay about…" doesn't match
    # artifact keywords that might appear in the essay topic text.
    if _ESSAY_PATTERNS.search(prompt):
        logger.info("[Router] Keyword fast-path → essay (prompt=%r)", prompt[:60])
        return "essay"
    if _ARTIFACT_PATTERNS.search(prompt):
        logger.info("[Router] Keyword fast-path → artifact (prompt=%r)", prompt[:60])
        return "artifact"
    return None  # Unknown → try LLM classifier or default to qa


class AgentRouter:
    def __init__(self):
        self.skills = {
            "qa": QASkill(),
            "essay": EssaySkill(),
            "artifact": ArtifactSkill(),
        }

    async def route_and_execute(
        self, prompt: str, context: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Classify the user's intent and execute the appropriate skill.

        Classification order:
        1. Keyword fast-path (no LLM call needed).
        2. LLM classifier (fallback for ambiguous prompts).
        3. Default to ``qa`` if the LLM call fails.
        """
        # --- Step 1: Keyword fast-path ---
        target_skill_name = _keyword_classify(prompt)

        if target_skill_name is None:
            # --- Step 2: LLM classifier fallback (only for ambiguous prompts) ---
            classification_prompt = (
                "Classify the user query into exactly one of these skills:\n"
                "- 'essay': If the user explicitly asks for an essay, article, write-up, "
                "blog post, newsletter, or a 'Ship30for30' style output.\n"
                "- 'artifact': If the user asks for a code file, HTML preview, template, "
                "roadmap, dashboard, spreadsheet, mock, or visual page.\n"
                "- 'qa': For any other general question, query about product, engineering, "
                "growth, or advice from Lenny's podcast.\n\n"
                'Query: "{prompt}"\n\n'
                "Respond with exactly one word from this list: qa, essay, artifact. "
                "Do not include punctuation, reasoning or quotes."
            ).format(prompt=prompt)

            try:
                llm = get_llm_provider()
                classification_result = await llm.generate(
                    messages=[{"role": "user", "content": classification_prompt}],
                    options={"num_predict": 10},  # classification needs ≤ 3 tokens
                )
                cleaned_result = (
                    classification_result.strip().lower().replace('"', "").replace("'", "")
                )
                logger.info(
                    "[Router] LLM classified %r as: %s", prompt[:40], cleaned_result
                )
                for skill_name in self.skills:
                    if skill_name in cleaned_result:
                        target_skill_name = skill_name
                        break
                else:
                    target_skill_name = "qa"
            except Exception as e:
                logger.error(
                    "[Router] LLM classification failed: %s — defaulting to 'qa'.", e
                )
                target_skill_name = "qa"

        logger.info("[Router] Dispatching to skill=%r for prompt=%r", target_skill_name, prompt[:60])
        skill = self.skills[target_skill_name]
        result = await skill.execute(prompt, context)
        result["skill_used"] = target_skill_name
        return result
