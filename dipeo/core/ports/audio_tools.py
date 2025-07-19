"""Audio tool port interfaces."""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from dipeo.models import SpeechToTextResult, TextToSpeechResult


@runtime_checkable
class SpeechToTextPort(Protocol):
    """Port for speech-to-text conversion services.
    
    This interface defines the contract for services that convert
    audio input into text transcriptions.
    """

    async def transcribe(
        self,
        audio_data: bytes | str,  # Raw bytes or base64 encoded
        format: str | None = None,  # Audio format (mp3, wav, etc.)
        language: str | None = None,  # Language hint
        **kwargs,
    ) -> "SpeechToTextResult":
        """Convert speech audio to text.
        
        Args:
            audio_data: Audio data as bytes or base64 string
            format: Audio format (e.g., 'mp3', 'wav', 'webm')
            language: Language code hint (e.g., 'en', 'es')
            **kwargs: Provider-specific options
            
        Returns:
            SpeechToTextResult with transcription and metadata
        """
        ...

    def supports_streaming(self) -> bool:
        """Check if the service supports streaming transcription."""
        ...

    def get_supported_formats(self) -> list[str]:
        """Get list of supported audio formats."""
        ...


@runtime_checkable
class TextToSpeechPort(Protocol):
    """Port for text-to-speech conversion services.
    
    This interface defines the contract for services that convert
    text into speech audio.
    """

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,  # Voice ID/name
        format: str = "mp3",  # Output format
        language: str | None = None,  # Language for synthesis
        **kwargs,
    ) -> "TextToSpeechResult":
        """Convert text to speech audio.
        
        Args:
            text: Text to convert to speech
            voice: Voice identifier (provider-specific)
            format: Output audio format
            language: Language code for synthesis
            **kwargs: Provider-specific options (speed, pitch, etc.)
            
        Returns:
            TextToSpeechResult with audio data and metadata
        """
        ...

    def get_available_voices(self) -> list[dict[str, str]]:
        """Get list of available voices with metadata."""
        ...

    def get_supported_formats(self) -> list[str]:
        """Get list of supported output formats."""
        ...