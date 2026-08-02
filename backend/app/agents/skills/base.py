from typing import List, Dict, Any, Optional

class BaseSkill:
    """Interface for an agent skill."""
    @property
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def description(self) -> str:
        raise NotImplementedError()

    async def execute(self, prompt: str, context: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Execute the skill and return a dict with key 'content' and optional 'artifact' structure."""
        raise NotImplementedError()
