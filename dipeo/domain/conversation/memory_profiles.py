"""Simplified memory management using profiles instead of separate modes."""

from enum import Enum, auto

from dipeo.diagram_generated import MemorySettings, MemoryView as MemoryViewEnum

from .memory_filters import MemoryView


class MemoryProfile(Enum):
    FULL = auto()
    FOCUSED = auto()
    MINIMAL = auto()
    GOLDFISH = auto()
    CUSTOM = auto()


class MemoryProfileFactory:
    
    _profiles = {
        MemoryProfile.FULL: MemorySettings(
            view=MemoryViewEnum.ALL_MESSAGES,
            max_messages=None,
            preserve_system=True
        ),
        MemoryProfile.FOCUSED: MemorySettings(
            view=MemoryViewEnum.CONVERSATION_PAIRS,
            max_messages=20,
            preserve_system=True
        ),
        MemoryProfile.MINIMAL: MemorySettings(
            view=MemoryViewEnum.SYSTEM_AND_ME,
            max_messages=5,
            preserve_system=True
        ),
        MemoryProfile.GOLDFISH: MemorySettings(
            view=MemoryViewEnum.CONVERSATION_PAIRS,
            max_messages=2,
            preserve_system=False
        ),
    }
    
    @classmethod
    def get_settings(cls, profile: MemoryProfile) -> MemorySettings:
        return cls._profiles[profile]
    
    @classmethod
    def custom(cls, view: MemoryViewEnum, max_messages: int | None = None) -> MemorySettings:
        return MemorySettings(
            view=view,
            max_messages=max_messages,
            preserve_system=True
        )