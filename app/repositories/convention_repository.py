import logging

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.convention import Convention

logger = logging.getLogger("uvicorn.error")


class ConventionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_convention(self):
        logger.info("[REPO] 모든 컨벤션 문서 조회")

        result = await self.db.execute(select(Convention))

        conventions = result.scalars().all()

        response = [
            {
                "convention_id": r.convention_id,
                "repo_id": r.repo_id,
                "filename": r.filename,
                "uploaded_by": r.uploaded_by,
            }
            for r in conventions
        ]

        return response

    async def get_convention_py_repo_id(self, repo_id: int) -> list[Convention]:
        stmt = select(Convention).where(Convention.repo_id == repo_id)
        result = await self.db.scalars(stmt)

        response = [
            {
                "convention_id": r.convention_id,
                "repo_id": r.repo_id,
                "filename": r.filename,
                "uploaded_by": r.uploaded_by,
            }
            for r in result
        ]

        return response

    async def create_repo_convention(
        self,
        repo_id: int,
        filename: str,
        filecontent: str,
        filehash: bytes,
        uploaded_by: int,
    ) -> Convention:
        stmt = (
            insert(Convention)
            .values(
                repo_id=repo_id,
                filename=filename,
                filecontent=filecontent,
                filehash=filehash,
                uploaded_by=uploaded_by,
            )
            .returning(Convention)
        )

        result = await self.db.execute(stmt)
        convention = result.scalar_one()

        return convention
