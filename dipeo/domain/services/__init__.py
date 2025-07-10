"""Domain modules."""

# Re-export domain modules as they're moved
# InputResolutionService moved to application layer
InputResolutionService = None
# FlowControlService moved to application layer
FlowControlService = None

# Import new services with try/except for backward compatibility
try:
    from .prompt import PromptBuilder
except ImportError:
    PromptBuilder = None

try:
    from .llm import LLMExecutor, LLMExecutionResult
except ImportError:
    LLMExecutor = None
    LLMExecutionResult = None

try:
    from .conversation import ConversationStateManager, MessageBuilder
except ImportError:
    ConversationStateManager = None
    MessageBuilder = None

# PersonJobOrchestrator moved to application layer
PersonJobOrchestrator = None

# Build exports list dynamically
__all__ = [
    "InputResolutionService",
]

if FlowControlService is not None:
    __all__.append("FlowControlService")

if PromptBuilder is not None:
    __all__.append("PromptBuilder")
if LLMExecutor is not None:
    __all__.extend(["LLMExecutor", "LLMExecutionResult"])
if ConversationStateManager is not None:
    __all__.extend(["ConversationStateManager", "MessageBuilder"])
if PersonJobOrchestrator is not None:
    __all__.append("PersonJobOrchestrator")
