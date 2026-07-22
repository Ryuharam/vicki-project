# /convention으로 받은 컨벤션 문서를 벡터db에 저장
from fastapi import APIRouter, HTTPException, UploadFile

from app.repositories.vector_repository import get_all_documents
from app.services.convention_service import upload_convention

router = APIRouter(prefix="/convention", tags=["convention"])


@router.get("")
def get_all():
    results = get_all_documents()

    return "\n".join([r for r in results])


@router.post("")
def create_documents(file: UploadFile, repo_id: int):

    with file.file as f:
        content_bytes = f.read()
        content_str = content_bytes.decode("utf-8")

    upload_convention(content=content_str, filename=file.filename, repo_id=repo_id)

    return {"filename": file.filename}


@router.delete("/{ids}")
def remove_documents():
    pass
