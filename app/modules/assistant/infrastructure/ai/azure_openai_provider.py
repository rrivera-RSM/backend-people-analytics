from __future__ import annotations

from app.modules.assistant.application.ports import (
    AIProviderRequest,
    AIProviderResponse,
)
from app.modules.assistant.infrastructure.ai.base import BaseAIProvider


class AzureOpenAIProvider(BaseAIProvider):
    def __init__(self, endpoint: str, model_name: str) -> None:
        super().__init__(provider_name="azure_openai", model_name=model_name)
        self.endpoint = endpoint

    async def generate_response(
        self,
        request: AIProviderRequest,
    ) -> AIProviderResponse:
        raise NotImplementedError(
            "AzureOpenAIProvider esta reservado para la integracion real."
        )
