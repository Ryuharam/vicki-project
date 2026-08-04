# import pytest

# from app.core.llm import build_llm, build_llm_chain


# def test_fallbacks_parsed_as_list(settings):
#     """LLM_FALLBACKS는 쉼표 구분 문자열에서 리스트로 파싱됩니다."""
#     assert settings.LLM_FALLBACKS == ["google_genai:gemini-2.5-flash"]


# def test_build_llm_selects_provider_from_spec(settings):
#     """spec 앞부분이 provider로 해석됩니다."""
#     model = build_llm("anthropic:claude-haiku-4-5-20251001", settings)

#     assert type(model).__name__ == "ChatAnthropic"


# def test_build_llm_requires_api_key(settings):
#     """키가 없는 provider를 지정하면 명확한 에러를 냅니다."""
#     settings_without_key = settings.model_copy(update={"GOOGLE_API_KEY": None})

#     with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
#         build_llm("google_genai:gemini-2.5-flash", settings_without_key)


# def test_ollama_needs_no_api_key(settings):
#     """키가 필요 없는 provider는 키 검사를 건너뜁니다."""
#     bare = settings.model_copy(
#         update={"GOOGLE_API_KEY": None, "ANTHROPIC_API_KEY": None}
#     )

#     model = build_llm("ollama:gemma4:e2b-mlx", bare)

#     assert type(model).__name__ == "ChatOllama"


# def test_build_llm_chain_wraps_fallbacks(settings):
#     """fallback이 있으면 RunnableWithFallbacks로 감쌉니다."""
#     chain = build_llm_chain(settings)

#     assert type(chain).__name__ == "RunnableWithFallbacks"


# def test_build_llm_chain_without_fallbacks_returns_bare_model(settings):
#     """fallback이 없으면 불필요한 래퍼를 씌우지 않습니다."""
#     solo = settings.model_copy(update={"LLM_FALLBACKS": []})

#     chain = build_llm_chain(solo)

#     assert type(chain).__name__ == "ChatAnthropic"
