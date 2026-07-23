# /convention으로 받은 컨벤션 문서를 벡터db에 저장
import logging
from fastapi import APIRouter, HTTPException, UploadFile

from app.repositories.vector_repository import get_all_documents, delete_documents
from app.services.convention_service import upload_convention

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/convention", tags=["convention"])


@router.get("")
def get_all():
    return get_all_documents()


@router.post("")
def create_documents(file: UploadFile, repo_id: int):

    with file.file as f:
        content_bytes = f.read()
        content_str = content_bytes.decode("utf-8")

    upload_convention(content=content_str, filename=file.filename, repo_id=repo_id)

    return {"filename": file.filename}


@router.delete("/repo/{repo_id}/file/{filename}")
def remove_documents(repo_id, filename):

    delete_documents(repo_id=repo_id, filename=filename)

    return {"result": "삭제완료"}
