"""Domain modules."""

# Re-export domain modules as they're moved
from .execution import ExecutionFlowService, InputResolutionService

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
    from .conversation import ConversationStateManager, MessagePreparator
except ImportError:
    ConversationStateManager = None
    MessagePreparator = None

try:
    from .person_job import PersonJobOrchestrator
except ImportError:
    PersonJobOrchestrator = None

# Build exports list dynamically
__all__ = [
    "ExecutionFlowService",
    "InputResolutionService",
]

if PromptBuilder is not None:
    __all__.append("PromptBuilder")
if LLMExecutor is not None:
    __all__.extend(["LLMExecutor", "LLMExecutionResult"])
if ConversationStateManager is not None:
    __all__.extend(["ConversationStateManager", "MessagePreparator"])
if PersonJobOrchestrator is not None:
    __all__.append("PersonJobOrchestrator")
