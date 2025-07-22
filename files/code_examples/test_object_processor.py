"""
Test processor for object content type.
Demonstrates receiving and returning complete data structures.
"""

def process_data(inputs):
    """Process user data and add statistics."""
    # The entire user_data object should be available
    user_data = inputs.get('user_data', {})
    
    # Access nested properties
    user_info = user_data.get('user_info', {})
    name = user_info.get('name', 'Unknown')
    age = user_info.get('age', 0)
    preferences = user_info.get('preferences', {})
    
    # Calculate some statistics
    stats = {
        'total_items': len(user_info) + len(preferences),
        'average_score': (age * 2.5) if age > 0 else 0,
        'preference_count': len(preferences)
    }
    
    # Return complete object structure
    return {
        'user_info': user_info,  # Pass through original data
        'result': f"Processed data for {name} (age {age})",
        'stats': stats,
        'metadata': {
            'processed_at': '2024-01-01T12:00:00Z',
            'version': '1.0'
        }
    }