from __future__ import annotations

from app.modules.assistant.application.ports import AIProviderPort


class BaseAIProvider(AIProviderPort):
    def __init__(self, provider_name: str, model_name: str = "") -> None:
        self._provider_name = provider_name
        self.model_name = model_name

    @property
    def provider_name(self) -> str:
        return self._provider_name
