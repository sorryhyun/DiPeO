"""Simplified memory management using profiles instead of separate modes."""

from enum import Enum, auto

from dipeo.diagram_generated import MemorySettings, MemoryView


class MemoryProfile(Enum):
    FULL = auto()
    FOCUSED = auto()
    MINIMAL = auto()
    GOLDFISH = auto()
    ONLY_ME = auto()
    ONLY_I_SENT = auto()
    CUSTOM = auto()


class MemoryProfileFactory:
    
    _profiles = {
        MemoryProfile.FULL: MemorySettings(
            view=MemoryView.ALL_MESSAGES,
            max_messages=None,
            preserve_system=True
        ),
        MemoryProfile.FOCUSED: MemorySettings(
            view=MemoryView.CONVERSATION_PAIRS,
            max_messages=20,
            preserve_system=True
        ),
        MemoryProfile.MINIMAL: MemorySettings(
            view=MemoryView.SYSTEM_AND_ME,
            max_messages=5,
            preserve_system=True
        ),
        MemoryProfile.ONLY_ME: MemorySettings(
            view=MemoryView.SENT_TO_ME,
            max_messages=3,
            preserve_system=True
        ),
        MemoryProfile.ONLY_I_SENT: MemorySettings(
            view=MemoryView.SENT_BY_ME,
            max_messages=None,  # No limit to preserve all my messages and system prompts
            preserve_system=True
        ),
        MemoryProfile.GOLDFISH: MemorySettings(
            view=MemoryView.SENT_TO_ME,
            max_messages=1,
            preserve_system=True
        ),
    }
    
    @classmethod
    def get_settings(cls, profile: MemoryProfile) -> MemorySettings:
        return cls._profiles[profile]
    
    @classmethod
    def custom(cls, view: MemoryView, max_messages: int | None = None) -> MemorySettings:
        return MemorySettings(
            view=view,
            max_messages=max_messages,
            preserve_system=True
        )