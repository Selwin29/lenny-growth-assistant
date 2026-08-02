import logging
from typing import List, Dict, Any
from app.agents.skills.qa_skill import QASkill
from app.agents.skills.essay_skill import EssaySkill
from app.agents.skills.artifact_skill import ArtifactSkill
from app.services.llm_service import get_llm_provider

logger = logging.getLogger(__name__)

class AgentRouter:
    def __init__(self):
        self.skills = {
            "qa": QASkill(),
            "essay": EssaySkill(),
            "artifact": ArtifactSkill()
        }

    async def route_and_execute(self, prompt: str, context: List[Dict[str, str]]) -> Dict[str, Any]:
        """Classify the user's intent and execute the appropriate skill."""
        classification_prompt = (
            "Classify the user query into exactly one of these skills:\n"
            "- 'essay': If the user explicitly asks for an essay, article, write-up, blog post, newsletter, or a 'Ship30for30' style output.\n"
            "- 'artifact': If the user asks for a code file, HTML preview, template, roadmap, dashboard, spreadsheet, mock, or visual page.\n"
            "- 'qa': For any other general question, query about product, engineering, growth, or advice from Lenny's podcast.\n\n"
            "Query: \"{prompt}\"\n\n"
            "Respond with exactly one word from this list: qa, essay, artifact. Do not include punctuation, reasoning or quotes."
        ).format(prompt=prompt)

        try:
            llm = get_llm_provider()
            classification_result = await llm.generate(
                messages=[{"role": "user", "content": classification_prompt}]
            )
            cleaned_result = classification_result.strip().lower().replace('"', '').replace("'", "")
            logger.info(f"Classified query '{prompt[:40]}...' as: {cleaned_result}")
            
            # Match classified skill or default to qa
            target_skill_name = "qa"
            for skill_name in self.skills.keys():
                if skill_name in cleaned_result:
                    target_skill_name = skill_name
                    break
        except Exception as e:
            logger.error(f"Router classification failed: {e}. Defaulting to 'qa'.")
            target_skill_name = "qa"

        logger.info(f"Executing skill '{target_skill_name}' for query.")
        skill = self.skills[target_skill_name]
        result = await skill.execute(prompt, context)
        # Add metadata on which skill was used
        result["skill_used"] = target_skill_name
        return result
