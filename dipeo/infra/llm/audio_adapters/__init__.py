"""Audio adapter implementations for various LLM services."""

from .openai_audio_adapter import OpenAIAudioAdapter
# from .gemini_audio_adapter import GeminiAudioAdapter

__all__ = [
    "OpenAIAudioAdapter",
    # "GeminiAudioAdapter",
]