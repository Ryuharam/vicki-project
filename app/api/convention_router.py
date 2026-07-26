# /convention으로 받은 컨벤션 문서를 벡터db에 저장
import logging

from fastapi import APIRouter, UploadFile

from app.api.deps import ContainerDep
from app.services.convention_service import upload_convention

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/convention", tags=["convention"])


@router.get("")
def get_all(container: ContainerDep):
    return container.repository.get_all_documents()


@router.post("")
def create_documents(file: UploadFile, repo_id: int, container: ContainerDep):

    with file.file as f:
        content_bytes = f.read()
        content_str = content_bytes.decode("utf-8")

    upload_convention(
        repository=container.repository,
        content=content_str,
        filename=file.filename,
        repo_id=repo_id,
    )

    return {"filename": file.filename}


@router.delete("/repo/{repo_id}/file/{filename}")
def remove_documents(repo_id: int, filename: str, container: ContainerDep):

    container.repository.delete_documents(repo_id=repo_id, filename=filename)

    return {"result": "삭제완료"}
