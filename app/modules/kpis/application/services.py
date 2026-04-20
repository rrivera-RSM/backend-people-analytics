from datetime import datetime
from app.modules.kpis.infrastructure.repo import KpisRepo


class KpisService:
    def __init__(self, read_repo: KpisRepo):
        self.read_repo = read_repo

    async def list_kpis(
        self,
        as_of: datetime | None = None,
        society: int | None = None,
        department: int | None = None,
        office: int | None = None,
        category: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await self.read_repo.list_kpis(
            as_of=as_of,
            society=society,
            department=department,
            office=office,
            category=category,
            limit=limit,
            offset=offset,
        )
