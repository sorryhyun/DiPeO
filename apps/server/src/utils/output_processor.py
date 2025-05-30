from typing import Any, Union, List, Dict


class OutputProcessor:
    """Centralized processor for handling PersonJob and other wrapped outputs."""
    
    @staticmethod
    def extract_value(value: Any) -> Any:
        """
        Extract actual value from wrapped outputs.
        
        This method handles PersonJob outputs and other wrapped formats,
        extracting the actual content value.
        
        Args:
            value: The value to process, which may be wrapped in a PersonJob output format
            
        Returns:
            The extracted value (text content for PersonJob outputs, original value otherwise)
        """
        if isinstance(value, dict) and value.get('_type') == 'personjob_output':
            return value.get('text', '')
        return value
    
    @staticmethod
    def extract_conversation_history(value: Any) -> List[Dict[str, str]]:
        """
        Extract conversation history from PersonJob output.
        
        Args:
            value: The value to process, which may contain conversation history
            
        Returns:
            List of conversation messages, empty list if not a PersonJob output
        """
        if isinstance(value, dict) and value.get('_type') == 'personjob_output':
            return value.get('conversation_history', [])
        return []
    
    @staticmethod
    def extract_metadata(value: Any) -> Dict[str, Any]:
        """
        Extract metadata from PersonJob output.
        
        Args:
            value: The value to process
            
        Returns:
            Dictionary of metadata, empty dict if not a PersonJob output
        """
        if isinstance(value, dict) and value.get('_type') == 'personjob_output':
            metadata = {}
            # Extract known metadata fields
            if 'cost' in value:
                metadata['cost'] = value['cost']
            if 'model' in value:
                metadata['model'] = value['model']
            if 'token_count' in value:
                metadata['token_count'] = value['token_count']
            if 'execution_time' in value:
                metadata['execution_time'] = value['execution_time']
            return metadata
        return {}
    
    @staticmethod
    def is_personjob_output(value: Any) -> bool:
        """
        Check if a value is a PersonJob output.
        
        Args:
            value: The value to check
            
        Returns:
            True if the value is a PersonJob output, False otherwise
        """
        return isinstance(value, dict) and value.get('_type') == 'personjob_output'
    
    @staticmethod
    def process_list(values: List[Any]) -> List[Any]:
        """
        Process a list of values, extracting PersonJob outputs.
        
        Args:
            values: List of values to process
            
        Returns:
            List of processed values with PersonJob outputs extracted
        """
        return [OutputProcessor.extract_value(v) for v in values]
    
    @staticmethod
    def create_personjob_output(
        text: str,
        conversation_history: List[Dict[str, str]] = None,
        cost: float = 0.0,
        model: str = None,
        token_count: int = 0
    ) -> Dict[str, Any]:
        """
        Create a PersonJob output format.
        
        Args:
            text: The output text
            conversation_history: List of conversation messages
            cost: The cost of the operation
            model: The model used
            token_count: Number of tokens used
            
        Returns:
            Dictionary in PersonJob output format
        """
        output = {
            '_type': 'personjob_output',
            'text': text
        }
        
        if conversation_history is not None:
            output['conversation_history'] = conversation_history
        if cost > 0:
            output['cost'] = cost
        if model:
            output['model'] = model
        if token_count > 0:
            output['token_count'] = token_count
            
        return output