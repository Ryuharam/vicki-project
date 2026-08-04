# /convention으로 받은 컨벤션 문서를 벡터db에 저장
import hashlib
import logging

from fastapi import APIRouter, UploadFile

from app.api.deps import ContainerDep, DbDep
from app.services.convention_service import ConventionService
from app.schemas.response import ConventionOut

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/convention", tags=["convention"])


@router.get("")
async def get_all(db: DbDep):
    logger.info("[ROUTER] get all")
    service = ConventionService(db)

    result = await service.get_all_conventions()

    return result


@router.get("/{repo_id}", response_model=list[ConventionOut])
async def get_convention_by_repo_id(repo_id: int, db: DbDep):
    service = ConventionService(db)

    return await service.get_repo_conventions(repo_id=repo_id)


@router.post("")
async def create_documents(file: UploadFile, repo_id: int, user_id: int, db: DbDep):

    with file.file as f:
        content_bytes = f.read()
        content_str = content_bytes.decode("utf-8")
        hash_bytes = hashlib.sha256(content_bytes).digest()

    service = ConventionService(db)

    result = await service.create_repo_convention(
        repo_id=repo_id,
        filename=file.filename,
        filecontent=content_str,
        filehash=hash_bytes,
        uploaded_by=user_id,
    )

    return {"convention_id": result.convention_id, "filename": result.filename}
