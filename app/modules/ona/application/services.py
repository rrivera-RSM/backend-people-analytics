from app.modules.ona.infrastructure.repo import OnaRepo
from app.modules.ona.schemas import (
    OnaGraphOut,
    OnaParticipationRateOut,
    OnaRelationsOut,
)


class OnaService:
    def __init__(self, read_repo: OnaRepo):
        self.read_repo = read_repo

    async def get_all_ona_relations(
        self, society_id: int | None = None
    ) -> OnaGraphOut:
        return await self.read_repo.get_all_ona_relations(
            society_id=society_id
        )

    async def get_ona_relations_by_employee_id(
        self, employee_id: int
    ) -> list[OnaRelationsOut]:
        return await self.read_repo.get_ona_relations_by_employee_id(
            employee_id=employee_id
        )

    async def get_ona_active_by_employee_id(self, employee_id: int):
        return await self.read_repo.get_ona_active_by_employee_id(
            employee_id=employee_id
        )

    async def get_participation_rate(
        self, society_id: int, office_id: int
    ) -> OnaParticipationRateOut | None:
        return await self.read_repo.get_participation_rate(
            society_id=society_id,
            office_id=office_id,
        )
