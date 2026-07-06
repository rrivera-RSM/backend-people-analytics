from __future__ import annotations

from app.modules.assistant.application.ports import (
    AIProviderRequest,
    AIProviderResponse,
)
from app.modules.assistant.infrastructure.ai.base import BaseAIProvider


class OpenAIAIProvider(BaseAIProvider):
    def __init__(self, api_key: str, model_name: str) -> None:
        super().__init__(provider_name="openai", model_name=model_name)
        self.api_key = api_key

    async def generate_response(
        self,
        request: AIProviderRequest,
    ) -> AIProviderResponse:
        raise NotImplementedError(
            "OpenAIAIProvider esta reservado para la integracion real."
        )
