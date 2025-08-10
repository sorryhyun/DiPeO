"""Utility for compiling Pydantic model definitions from string code."""

import ast
import logging
from typing import Any, Type

from pydantic import BaseModel

logger = logging.getLogger(__name__)


def compile_pydantic_model(code_str: str) -> Type[BaseModel] | None:
    """
    Compile a string containing Pydantic model definitions into actual BaseModel classes.
    Automatically injects necessary imports if not present.
    
    Args:
        code_str: Python code string defining Pydantic models
        
    Returns:
        The main response model class if successful, None otherwise
    """
    try:
        # Check if imports are already present, if not add them
        if 'from pydantic import' not in code_str and 'import pydantic' not in code_str:
            # Prepend necessary imports
            auto_imports = """from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from dipeo.core.type_defs import JsonValue, JsonDict, JsonList, SimpleJsonValue

"""
            code_str = auto_imports + code_str
        
        # Create a namespace for execution
        namespace = {
            'BaseModel': BaseModel,
            'Field': __import__('pydantic').Field,
            'Enum': __import__('enum').Enum,
            'List': __import__('typing').List,
            'Optional': __import__('typing').Optional,
            'Dict': __import__('typing').Dict,
            'Any': __import__('typing').Any,
            'Union': __import__('typing').Union,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            # Import JsonValue types from type_defs
            'JsonValue': __import__('dipeo.core.type_defs', fromlist=['JsonValue']).JsonValue,
            'JsonDict': __import__('dipeo.core.type_defs', fromlist=['JsonDict']).JsonDict,
            'JsonList': __import__('dipeo.core.type_defs', fromlist=['JsonList']).JsonList,
            'SimpleJsonValue': __import__('dipeo.core.type_defs', fromlist=['SimpleJsonValue']).SimpleJsonValue,
        }
        
        # Parse the code to find class definitions
        tree = ast.parse(code_str)
        
        # Execute the code
        exec(compile(tree, '<string>', 'exec'), namespace)
        
        # Find the main response model (typically the last BaseModel subclass defined)
        response_model = None
        for name, obj in namespace.items():
            if isinstance(obj, type) and issubclass(obj, BaseModel) and obj != BaseModel:
                response_model = obj
                # Look for a class explicitly named "Response" or ending with "Response"
                if name == "Response" or name.endswith("Response"):
                    return obj
        
        # If no Response class found, return the last BaseModel found
        if response_model:
            logger.debug(f"Compiled Pydantic model: {response_model.__name__}")
            return response_model
            
        logger.warning("No BaseModel class found in provided code")
        return None
        
    except SyntaxError as e:
        logger.error(f"Syntax error in Pydantic model code: {e}")
        return None
    except Exception as e:
        logger.error(f"Error compiling Pydantic model: {e}")
        return None


def is_pydantic_code(text_format: str) -> bool:
    """
    Check if the text_format string contains Pydantic model definitions.
    
    Args:
        text_format: String to check
        
    Returns:
        True if it appears to be Python code with Pydantic models
    """
    if not isinstance(text_format, str):
        return False
    
    # Check for common Pydantic/Python class patterns
    indicators = [
        'class ',           # Python class definition
        '(BaseModel)',      # Explicit BaseModel inheritance
        '(str, Enum)',      # String enum pattern
        ': str',            # Type hints
        ': int',
        ': float',
        ': bool',
        ': List[',          # List type hint
        ': Optional[',      # Optional type hint
        ': Dict[',          # Dict type hint
        'model_rebuild()',  # Pydantic specific method
        'from pydantic',    # Explicit import
        'from enum import', # Enum import
    ]
    
    # Must have at least a class definition to be considered Pydantic code
    has_class = 'class ' in text_format
    has_type_hints = any(indicator in text_format for indicator in [': str', ': int', ': float', ': bool', ': List[', ': Optional[', ': Dict['])
    
    return has_class and (has_type_hints or 'BaseModel' in text_format or 'Enum' in text_format)