from abc import ABC, abstractmethod
from typing import AsyncGenerator
from src.classifier.schemas import ClassifierOutput

class BaseAgent(ABC):
    @abstractmethod
    async def run(
        self,
        query: str,
        classification: ClassifierOutput,
        user_context: dict,
        session_id: str
    ) -> AsyncGenerator[str, None]:
        pass
