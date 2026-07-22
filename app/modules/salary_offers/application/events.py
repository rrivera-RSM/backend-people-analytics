from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppManagerIdentity:
    employee_id: int
    first_name: str
    last_name: str
    email: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


@dataclass(frozen=True)
class AllManageesHaveProposal:
    app_manager: AppManagerIdentity
    year: int
