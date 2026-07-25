import logging

from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

provider = settings.PROVIDER
logger.info(f"[llm] provider: {provider}")


if provider == "google":
    from langchain_google_genai import ChatGoogleGenerativeAI

    model = settings.GOOGLE_MODEL

    _llm = ChatGoogleGenerativeAI(model=model, max_retries=1)
elif provider == "anthropic":
    from langchain_anthropic import ChatAnthropic

    model = settings.ANTHROPIC_MODEL

    _llm = ChatAnthropic(model=model, max_retries=1)
else:
    from langchain_ollama import ChatOllama

    model = settings.OLLAMA_MODEL

    _llm = ChatOllama(model=model)

logger.info(f"model: {model}")


def get_model():
    return _llm
