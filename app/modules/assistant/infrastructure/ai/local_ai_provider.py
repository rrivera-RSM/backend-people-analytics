from __future__ import annotations

from app.modules.assistant.application.ports import (
    AIProviderRequest,
    AIProviderResponse,
)
from app.modules.assistant.infrastructure.ai.base import BaseAIProvider


class LocalAIProvider(BaseAIProvider):
    def __init__(self, endpoint: str, model_name: str = "") -> None:
        super().__init__(provider_name="local", model_name=model_name)
        self.endpoint = endpoint

    async def generate_response(
        self,
        request: AIProviderRequest,
    ) -> AIProviderResponse:
        raise NotImplementedError(
            "LocalAIProvider esta reservado para una integracion local."
        )
