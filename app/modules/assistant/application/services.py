from __future__ import annotations

from app.modules.assistant.application.ports import (
    AIMessage,
    AIProviderPort,
    AIProviderRequest,
)
from app.modules.assistant.application.tool_registry import AssistantToolRegistry
from app.modules.assistant.schemas import (
    AssistantChatRequest,
    AssistantChatResponse,
)


class AssistantService:
    def __init__(
        self,
        ai_provider: AIProviderPort,
        tool_registry: AssistantToolRegistry,
    ) -> None:
        self.ai_provider = ai_provider
        self.tool_registry = tool_registry

    async def handle_message(
        self,
        request: AssistantChatRequest,
    ) -> AssistantChatResponse:
        message = request.message.strip()
        if not message:
            raise ValueError("El mensaje no puede estar vacio")

        conversation = [
            AIMessage(role=item.role, content=item.content)
            for item in request.conversation
            if item.content.strip()
        ]
        tool_results = await self.tool_registry.build_context(
            employee_id=request.employee_id,
        )

        provider_response = await self.ai_provider.generate_response(
            AIProviderRequest(
                employee_id=request.employee_id,
                message=message,
                conversation=conversation,
                tool_results=tool_results,
            )
        )

        return AssistantChatResponse(
            answer=provider_response.answer,
            used_tools=provider_response.used_tools,
            provider=provider_response.provider,
        )
