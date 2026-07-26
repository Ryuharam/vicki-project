import logging

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from app.core.config import AppSettings

logger = logging.getLogger("uvicorn.error")

_API_KEY_SETTING = {
    "google_genai": "GOOGLE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def _rate_limit_errors() -> tuple[type[BaseException], ...]:
    """설치된 provider 기준으로 fallback을 발동시킬 예외 목록을 만듭니다."""
    errors: list[type[BaseException]] = []

    try:
        from anthropic import RateLimitError

        errors.append(RateLimitError)
    except ImportError:
        pass

    try:
        from google.genai.errors import ClientError

        errors.append(ClientError)
    except ImportError:
        pass

    return tuple(errors)


def build_llm(spec: str, settings: AppSettings, **kwargs) -> BaseChatModel:
    """ "provider:model" 스펙으로 채팅 모델 하나를 생성합니다."""
    provider = spec.split(":", 1)[0]

    setting_name = _API_KEY_SETTING.get(provider)
    if setting_name:
        api_key = getattr(settings, setting_name)
        if not api_key:
            raise ValueError(f"{spec} 를 사용하려면 {setting_name} 가 필요합니다.")
        kwargs["api_key"] = api_key

    logger.info(f"[llm] build {spec}")

    return init_chat_model(spec, max_retries=1, **kwargs)


def build_llm_chain(settings: AppSettings) -> BaseChatModel:
    """주 모델과 대체 모델을 묶은 체인을 만듭니다."""
    primary = build_llm(settings.LLM_PRIMARY, settings)

    if not settings.LLM_FALLBACKS:
        return primary

    fallbacks = [build_llm(spec, settings) for spec in settings.LLM_FALLBACKS]
    handled = _rate_limit_errors()

    if not handled:
        logger.warning("[llm] 잡을 수 있는 예외가 없어 fallback을 건너뜁니다.")
        return primary

    logger.info(f"[llm] fallbacks: {settings.LLM_FALLBACKS}")
    return primary.with_fallbacks(fallbacks, exceptions_to_handle=handled)
