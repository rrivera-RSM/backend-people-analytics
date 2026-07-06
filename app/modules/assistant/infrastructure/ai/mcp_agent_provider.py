from __future__ import annotations

from app.modules.assistant.application.ports import (
    AIProviderRequest,
    AIProviderResponse,
)
from app.modules.assistant.infrastructure.ai.base import BaseAIProvider


class MCPAgentProvider(BaseAIProvider):
    def __init__(self, server_url: str, model_name: str = "") -> None:
        super().__init__(provider_name="mcp", model_name=model_name)
        self.server_url = server_url

    async def generate_response(
        self,
        request: AIProviderRequest,
    ) -> AIProviderResponse:
        raise NotImplementedError(
            "MCPAgentProvider esta reservado para la integracion agentica."
        )
