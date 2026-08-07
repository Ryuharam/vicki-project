import os
import logging
import logging.config

LOG_DIR = "logs"

# 콘솔과 app.log에 남길 최소 레벨. 배포에서는 LOG_LEVEL=ERROR 처럼 올려서 줄입니다.
# error.log는 이 값과 무관하게 항상 ERROR만 기록합니다.
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# LOG_LEVEL을 CRITICAL로 올리더라도 error.log가 비지 않도록 루트는 ERROR 이하로 유지합니다.
_ROOT_LEVEL = logging.getLevelName(
    min(logging.getLevelNamesMapping().get(LOG_LEVEL, logging.INFO), logging.ERROR)
)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
        },
        "json": {
            "format": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s", "file":"%(filename)s", "line": "%(lineno)d"}'
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": LOG_LEVEL,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "detailed",
            "filename": f"{LOG_DIR}/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "level": LOG_LEVEL,
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "detailed",
            "filename": f"{LOG_DIR}/error.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "level": "ERROR",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console", "file", "error_file"],
            "level": _ROOT_LEVEL,
            "propagate": False,
        },
        "uvicorn": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "httpx": {"level": "WARNING"},
        "httpcore": {"level": "WARNING"},
        "uvicorn.error": {
            "handlers": ["console", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


def setup_logging() -> None:
    """로그 디렉토리를 만들고 LOGGING_CONFIG를 적용합니다.

    애플리케이션 임포트 시점에 한 번만 호출합니다.
    각 모듈은 `logging.getLogger(__name__)` 으로 로거를 가져다 씁니다.
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)
