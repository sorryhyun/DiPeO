"""File extension value object."""
from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class FileExtension:
    
    value: str
    
    COMMON_EXTENSIONS: ClassVar[set[str]] = {
        '.txt', '.md', '.pdf', '.doc', '.docx', '.rtf',
        '.json', '.yaml', '.yml', '.xml', '.csv', '.tsv',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs',
        '.log', '.config', '.env', '.ini'
    }
    
    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("File extension cannot be empty")
        
        if not self.value.startswith('.'):
            object.__setattr__(self, 'value', f'.{self.value}')
    
    @property
    def without_dot(self) -> str:
        return self.value.lstrip('.')
    
    @property
    def is_text_format(self) -> bool:
        text_formats = {'.txt', '.md', '.json', '.yaml', '.yml', '.xml', '.csv', '.tsv', '.log', '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.env', '.ini', '.config'}
        return self.value.lower() in text_formats
    
    @property
    def is_binary_format(self) -> bool:
        return not self.is_text_format
    
    def is_allowed(self, allowed_extensions: set[str]) -> bool:
        return self.value.lower() in {ext.lower() for ext in allowed_extensions}
    
    def __str__(self) -> str:
        return self.value