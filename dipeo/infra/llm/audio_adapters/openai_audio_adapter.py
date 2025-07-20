"""Audio tool adapters for LLM providers."""

import base64
import logging
from typing import Any

from openai import AsyncOpenAI, OpenAI

from dipeo.core.ports import SpeechToTextPort, TextToSpeechPort
from dipeo.models import SpeechToTextResult, TextToSpeechResult

logger = logging.getLogger(__name__)


class OpenAIAudioAdapter(SpeechToTextPort, TextToSpeechPort):
    """OpenAI implementation for audio tools (speech-to-text and text-to-speech)."""
    
    def __init__(self, api_key: str, base_url: str | None = None):
        """Initialize OpenAI audio adapter.
        
        Args:
            api_key: OpenAI API key
            base_url: Optional base URL for API calls
        """
        self.api_key = api_key
        self.base_url = base_url
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        # Available voices for TTS
        self._voices = [
            {"id": "alloy", "name": "Alloy", "gender": "neutral"},
            {"id": "echo", "name": "Echo", "gender": "male"},
            {"id": "fable", "name": "Fable", "gender": "neutral"},
            {"id": "onyx", "name": "Onyx", "gender": "male"},
            {"id": "nova", "name": "Nova", "gender": "female"},
            {"id": "shimmer", "name": "Shimmer", "gender": "female"},
        ]
        
        # Supported formats
        self._stt_formats = ["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"]
        self._tts_formats = ["mp3", "opus", "aac", "flac", "wav", "pcm"]
    
    async def transcribe(
        self,
        audio_data: bytes | str,
        format: str | None = None,
        language: str | None = None,
        **kwargs,
    ) -> SpeechToTextResult:
        """Convert speech audio to text using OpenAI Whisper.
        
        Args:
            audio_data: Audio data as bytes or base64 string
            format: Audio format (will be auto-detected if not provided)
            language: Language code hint (e.g., 'en', 'es')
            **kwargs: Additional options like model, prompt, temperature
            
        Returns:
            SpeechToTextResult with transcription and metadata
        """

        """ speech_to_text
        from openai import OpenAI
        client = OpenAI()

        audio_file = open("speech.mp3", "rb")
        transcript = client.audio.transcriptions.create(
          model="gpt-4o-transcribe",
          file=audio_file
        )

        """

        try:
            # Convert base64 to bytes if needed
            if isinstance(audio_data, str):
                audio_bytes = base64.b64decode(audio_data)
            else:
                audio_bytes = audio_data
            
            # Prepare parameters
            model = kwargs.get("model", "whisper-1")
            temperature = kwargs.get("temperature", 0)
            prompt = kwargs.get("prompt")
            response_format = kwargs.get("response_format", "verbose_json")
            
            # Create file-like object
            import io
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = f"audio.{format or 'mp3'}"
            
            # Make transcription request
            params = {
                "model": model,
                "file": audio_file,
                "response_format": response_format,
                "temperature": temperature,
            }
            
            if language:
                params["language"] = language
            if prompt:
                params["prompt"] = prompt
            
            response = await self.async_client.audio.transcriptions.create(**params)
            
            # Process response based on format
            if response_format == "verbose_json" and hasattr(response, "segments"):
                segments = [
                    {
                        "text": seg.text,
                        "start": seg.start,
                        "end": seg.end,
                    }
                    for seg in response.segments
                ] if response.segments else None
                
                return SpeechToTextResult(
                    text=response.text,
                    language=getattr(response, "language", language),
                    segments={"segments": segments} if segments else None,
                )
            else:
                # Simple text response
                return SpeechToTextResult(
                    text=response.text if hasattr(response, "text") else str(response),
                    language=language,
                )
                
        except Exception as e:
            logger.error(f"OpenAI speech-to-text error: {e}")
            raise
    
    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        format: str = "mp3",
        language: str | None = None,
        **kwargs,
    ) -> TextToSpeechResult:
        """Convert text to speech using OpenAI TTS.
        
        Args:
            text: Text to convert to speech
            voice: Voice ID (alloy, echo, fable, onyx, nova, shimmer)
            format: Output format (mp3, opus, aac, flac, wav, pcm)
            language: Language is auto-detected by OpenAI
            **kwargs: Additional options like model, speed
            
        Returns:
            TextToSpeechResult with audio data and metadata
        """

        """ text_to_speech
        from pathlib import Path
        import openai

        speech_file_path = Path(__file__).parent / "speech.mp3"
        with openai.audio.speech.with_streaming_response.create(
          model="gpt-4o-mini-tts",
          voice="alloy",
          input="The quick brown fox jumped over the lazy dog."
        ) as response:
          response.stream_to_file(speech_file_path)

        """
        try:
            # Prepare parameters
            model = kwargs.get("model", "tts-1")  # or "tts-1-hd" for higher quality
            voice = voice or "alloy"
            speed = kwargs.get("speed", 1.0)  # 0.25 to 4.0
            
            # Validate voice
            if voice not in [v["id"] for v in self._voices]:
                logger.warning(f"Unknown voice '{voice}', using 'alloy'")
                voice = "alloy"
            
            # Validate format
            if format not in self._tts_formats:
                logger.warning(f"Unsupported format '{format}', using 'mp3'")
                format = "mp3"
            
            # Make TTS request
            response = await self.async_client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format=format,
                speed=speed,
            )
            
            # Get audio data as bytes
            audio_bytes = response.read()
            
            # Convert to base64
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
            
            # Estimate duration (rough approximation based on text length and speed)
            # This is a placeholder - actual duration would need audio analysis
            words = len(text.split())
            wpm = 150 * speed  # Approximate words per minute
            duration = (words / wpm) * 60  # Duration in seconds
            
            return TextToSpeechResult(
                audio_data=audio_base64,
                format=format,
                duration=duration,
                voice=voice,
            )
            
        except Exception as e:
            logger.error(f"OpenAI text-to-speech error: {e}")
            raise
    
    def supports_streaming(self) -> bool:
        """OpenAI supports streaming for real-time transcription."""
        return True
    
    def get_supported_formats(self) -> list[str]:
        """Get list of supported audio formats for STT."""
        return self._stt_formats
    
    def get_available_voices(self) -> list[dict[str, str]]:
        """Get list of available voices with metadata."""
        return self._voices
    
    def get_supported_formats(self) -> list[str]:
        """Get list of supported output formats for TTS."""
        return self._tts_formats