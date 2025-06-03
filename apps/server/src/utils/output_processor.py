from typing import Any, List, Dict


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
            if 'token_count' in value:
                metadata['token_count'] = value['token_count']
            if 'input_tokens' in value:
                metadata['input_tokens'] = value['input_tokens']
            if 'output_tokens' in value:
                metadata['output_tokens'] = value['output_tokens']
            if 'cached_tokens' in value:
                metadata['cached_tokens'] = value['cached_tokens']
            if 'model' in value:
                metadata['model'] = value['model']
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
        token_count: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cached_tokens: int = 0,
        model: str = None
    ) -> Dict[str, Any]:
        """
        Create a PersonJob output format.
        
        Args:
            text: The output text
            conversation_history: List of conversation messages
            token_count: Total number of tokens used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cached_tokens: Number of cached tokens
            model: The model used
            
        Returns:
            Dictionary in PersonJob output format
        """
        output = {
            '_type': 'personjob_output',
            'text': text
        }
        
        if conversation_history is not None:
            output['conversation_history'] = conversation_history
        if token_count > 0:
            output['token_count'] = token_count
        if input_tokens > 0:
            output['input_tokens'] = input_tokens
        if output_tokens > 0:
            output['output_tokens'] = output_tokens
        if cached_tokens > 0:
            output['cached_tokens'] = cached_tokens
        if model:
            output['model'] = model
            
        return output