# custom_exception.py : 부모 예외 클래스 & 전역 예외 핸들러


class BaseAPIException(Exception):
    status_code: int = 500
    detail: str = "서버 내부 오류"


class DuplicateConventionException(BaseAPIException):
    status_code = 409
    detail = "이미 등록된 컨벤션 문서입니다."


class UserNotFoundException(BaseAPIException):
    status_code = 404
    detail = "존재하지 않는 유저입니다."


class RepositoryNotFoundException(BaseAPIException):
    status_code = 404
    detail = "존재하지 않는 레포지토리입니다."
