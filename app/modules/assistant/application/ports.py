from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class AIMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class AIToolResult:
    name: str
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class AIProviderRequest:
    employee_id: int
    message: str
    conversation: list[AIMessage] = field(default_factory=list)
    tool_results: list[AIToolResult] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AIProviderResponse:
    answer: str
    used_tools: list[str] = field(default_factory=list)
    provider: str = "unknown"


class AIProviderPort(Protocol):
    @property
    def provider_name(self) -> str:
        ...

    async def generate_response(
        self,
        request: AIProviderRequest,
    ) -> AIProviderResponse:
        ...
