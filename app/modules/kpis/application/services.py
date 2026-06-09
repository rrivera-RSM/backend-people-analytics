from datetime import datetime
from app.modules.kpis.infrastructure.repo import KpisRepo


class KpisService:
    def __init__(self, read_repo: KpisRepo):
        self.read_repo = read_repo

    async def list_kpis(
        self,
        as_of: datetime | None = None,
        society_id: int | None = None,
        department_id: int | None = None,
        office_id: int | None = None,
        category_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await self.read_repo.list_kpis(
            as_of=as_of,
            society_id=society_id,
            department_id=department_id,
            office_id=office_id,
            category_id=category_id,
            limit=limit,
            offset=offset,
        )
