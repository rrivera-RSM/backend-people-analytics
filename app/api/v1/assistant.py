from fastapi import APIRouter, Depends, HTTPException, Security

from app.api.deps import get_assistant_service
from app.auth import azure_scheme
from app.modules.assistant.application.services import AssistantService
from app.modules.assistant.schemas import (
    AssistantChatRequest,
    AssistantChatResponse,
)

assistant_router = APIRouter(
    prefix="/assistant",
    tags=["assistant"],
    dependencies=[Security(azure_scheme, scopes=["user_impersonation"])],
)


@assistant_router.post(
    "/chat",
    response_model=AssistantChatResponse,
    dependencies=[Depends(azure_scheme)],
)
async def chat_with_assistant(
    payload: AssistantChatRequest,
    service: AssistantService = Depends(get_assistant_service),
) -> AssistantChatResponse:
    try:
        return await service.handle_message(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc))
