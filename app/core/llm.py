import os
import logging

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("uvicorn.error")

provider = str(os.getenv("PROVIDER")).lower()
logger.info(f"[llm] provider: {provider}")


if provider == "google":
    from langchain_google_genai import ChatGoogleGenerativeAI

    model = os.getenv("GOOGLE_MODEL")

    _llm = ChatGoogleGenerativeAI(model=model, max_retries=1)
elif provider == "anthropic":
    from langchain_anthropic import ChatAnthropic

    model = os.getenv("ANTHROPIC_MODEL")

    _llm = ChatAnthropic(model=model, max_retries=1)
else:
    from langchain_ollama import ChatOllama

    model = os.getenv("OLLAMA_MODEL")

    _llm = ChatOllama(model=model)

logger.info(f"model: {model}")


def get_model():
    return _llm
