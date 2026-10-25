from typing import Optional, Any
from src.core.config import settings

def get_llm(provider: Optional[str] = None, model_name: Optional[str] = None, temperature: float = 0.0) -> Any:
    prov = provider or settings.DEFAULT_LLM_PROVIDER
    mod = model_name or settings.DEFAULT_MODEL_NAME

    if prov == "openai" and settings.OPENAI_API_KEY and "your_openai" not in settings.OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=mod, api_key=settings.OPENAI_API_KEY, temperature=temperature)
        except Exception as e:
            print(f"[Warning] Failed to initialize ChatOpenAI ({e}), using mock LLM.")

    elif prov == "anthropic" and settings.ANTHROPIC_API_KEY and "your_anthropic" not in settings.ANTHROPIC_API_KEY:
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model=mod, api_key=settings.ANTHROPIC_API_KEY, temperature=temperature)
        except Exception as e:
            print(f"[Warning] Failed to initialize ChatAnthropic ({e}), using mock LLM.")

    elif prov == "gemini" and settings.GEMINI_API_KEY and "your_gemini" not in settings.GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=mod, google_api_key=settings.GEMINI_API_KEY, temperature=temperature)
        except Exception as e:
            print(f"[Warning] Failed to initialize ChatGoogleGenerativeAI ({e}), using mock LLM.")

    # Return None if no live provider is configured; nodes will handle fallback gracefully
    return None
