import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.convention_repository import ConventionRepository

logger = logging.getLogger("uvicorn.error")


class ConventionService:
    def __init__(self, db: AsyncSession):
        self.repository = ConventionRepository(db)
        self.db = db
        # post, delete의 경우 self.db.commit() 하기

    async def get_all_conventions(self):
        logger.info("[SERVICE] get all")
        result = await self.repository.get_all_convention()

        return result

    async def get_repo_conventions(self, repo_id: int):
        logger.info("[SERVICE] get_repo_conventions")
        result = await self.repository.get_convention_py_repo_id(repo_id=repo_id)
        return result

    async def create_repo_convention(
        self,
        repo_id: int,
        filename: str,
        filecontent: str,
        filehash: str,
        uploaded_by: int,
    ):
        logger.info("[SERVICE] create_repo_convention")

        try:
            result = await self.repository.create_repo_convention(
                repo_id=repo_id,
                filename=filename,
                filecontent=filecontent,
                filehash=filehash,
                uploaded_by=uploaded_by,
            )

            await self.db.commit()
            return result
        except IntegrityError:
            await self.db.rollback()
            logger.error("이미 존재하는 파일")
            # TODO: Custom Error raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error: {e}")
            raise
