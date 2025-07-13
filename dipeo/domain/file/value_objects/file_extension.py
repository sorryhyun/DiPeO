"""File extension value object."""
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class FileExtension:
    """Represents a file extension with validation and behavior."""
    
    value: str
    
    # Common file extensions for validation
    COMMON_EXTENSIONS: ClassVar[set[str]] = {
        # Document formats
        '.txt', '.md', '.pdf', '.doc', '.docx', '.rtf',
        # Data formats
        '.json', '.yaml', '.yml', '.xml', '.csv', '.tsv',
        # Image formats
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
        # Archive formats
        '.zip', '.tar', '.gz', '.rar', '.7z',
        # Code formats
        '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs',
        # Other
        '.log', '.config', '.env', '.ini'
    }
    
    def __post_init__(self) -> None:
        """Validate the file extension."""
        if not self.value:
            raise ValueError("File extension cannot be empty")
        
        # Ensure extension starts with a dot
        if not self.value.startswith('.'):
            object.__setattr__(self, 'value', f'.{self.value}')
    
    @property
    def without_dot(self) -> str:
        """Return the extension without the leading dot."""
        return self.value.lstrip('.')
    
    @property
    def is_text_format(self) -> bool:
        """Check if this is a text-based file format."""
        text_formats = {'.txt', '.md', '.json', '.yaml', '.yml', '.xml', '.csv', '.tsv', '.log', '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.env', '.ini', '.config'}
        return self.value.lower() in text_formats
    
    @property
    def is_binary_format(self) -> bool:
        """Check if this is a binary file format."""
        return not self.is_text_format
    
    def is_allowed(self, allowed_extensions: set[str]) -> bool:
        """Check if this extension is in the allowed set."""
        return self.value.lower() in {ext.lower() for ext in allowed_extensions}
    
    def __str__(self) -> str:
        """String representation."""
        return self.value