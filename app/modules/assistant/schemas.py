from pydantic import BaseModel, Field


class AssistantMessageIn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=8000)


class AssistantChatRequest(BaseModel):
    employee_id: int = Field(gt=0)
    message: str = Field(min_length=1, max_length=8000)
    conversation: list[AssistantMessageIn] = Field(default_factory=list)


class AssistantChatResponse(BaseModel):
    answer: str
    used_tools: list[str] = Field(default_factory=list)
    provider: str
