from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseProvider(ABC):
    @abstractmethod
    async def generate_completion(self, request: Any, api_key: str) -> Dict[str, Any]:
        """
        Generate an LLM completion for the given gateway request wrapper.
        """
        pass
