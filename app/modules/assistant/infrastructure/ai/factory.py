from __future__ import annotations

from app.modules.assistant.application.ports import AIProviderPort
from app.modules.assistant.infrastructure.ai.azure_openai_provider import (
    AzureOpenAIProvider,
)
from app.modules.assistant.infrastructure.ai.local_ai_provider import (
    LocalAIProvider,
)
from app.modules.assistant.infrastructure.ai.mcp_agent_provider import (
    MCPAgentProvider,
)
from app.modules.assistant.infrastructure.ai.mock_provider import (
    MockAIProvider
)
from app.modules.assistant.infrastructure.ai.openai_provider import (
    OpenAIAIProvider,
)
from settings import Settings


def build_ai_provider(settings: Settings) -> AIProviderPort:
    provider = (settings.ASSISTANT_AI_PROVIDER or "mock").strip().lower()

    if provider == "mock":
        return MockAIProvider()

    if provider == "openai":
        return OpenAIAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.ASSISTANT_MODEL_NAME,
        )

    if provider == "mcp":
        return MCPAgentProvider(
            server_url=settings.ASSISTANT_MCP_SERVER_URL,
            model_name=settings.ASSISTANT_MODEL_NAME,
        )

    if provider == "azure_openai":
        return AzureOpenAIProvider(
            endpoint=settings.ASSISTANT_AZURE_OPENAI_ENDPOINT,
            model_name=settings.ASSISTANT_MODEL_NAME,
        )

    if provider == "local":
        return LocalAIProvider(
            endpoint=settings.ASSISTANT_LOCAL_AI_ENDPOINT,
            model_name=settings.ASSISTANT_MODEL_NAME,
        )

    raise ValueError(f"Proveedor de IA no soportado: {provider}")
