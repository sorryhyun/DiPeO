"""Test fixtures for diagram data."""

from typing import Dict, Any


class DiagramFixtures:
    """Collection of diagram fixtures for testing."""
    
    @staticmethod
    def simple_linear_diagram() -> Dict[str, Any]:
        """Start -> PersonJob -> Endpoint diagram."""
        return {
            "nodes": [
                {
                    "id": "start1",
                    "type": "start",
                    "position": {"x": 0, "y": 0},
                    "data": {"id": "start1", "label": "Start"}
                },
                {
                    "id": "person1",
                    "type": "person_job",
                    "position": {"x": 200, "y": 0},
                    "data": {
                        "id": "person1",
                        "label": "AI Assistant",
                        "personId": "assistant1",
                        "prompt": "You are a helpful AI assistant. Respond to the user's question."
                    }
                },
                {
                    "id": "end1",
                    "type": "endpoint",
                    "position": {"x": 400, "y": 0},
                    "data": {"id": "end1", "label": "End"}
                }
            ],
            "arrows": [
                {
                    "id": "arrow-1",
                    "source": "start1",
                    "target": "person1",
                    "type": "customArrow",
                    "data": {
                        "id": "arrow-data-1",
                        "sourceBlockId": "start1",
                        "targetBlockId": "person1",
                        "label": "",
                        "contentType": "variable"
                    }
                },
                {
                    "id": "arrow-2",
                    "source": "person1",
                    "target": "end1",
                    "type": "customArrow",
                    "data": {
                        "id": "arrow-data-2",
                        "sourceBlockId": "person1",
                        "targetBlockId": "end1",
                        "label": "",
                        "contentType": "variable"
                    }
                }
            ],
            "persons": [
                {
                    "id": "assistant1",
                    "name": "AI Assistant",
                    "service": "openai",
                    "model": "gpt-3.5-turbo",
                    "apiKeyId": "test-key-1"
                }
            ],
            "apiKeys": [
                {
                    "id": "test-key-1",
                    "name": "Test OpenAI Key",
                    "service": "openai"
                }
            ]
        }
    
    @staticmethod
    def branching_diagram() -> Dict[str, Any]:
        """Diagram with condition node and branches."""
        return {
            "nodes": [
                {
                    "id": "start1",
                    "type": "start",
                    "position": {"x": 0, "y": 0},
                    "data": {"id": "start1", "label": "Start"}
                },
                {
                    "id": "condition1",
                    "type": "condition",
                    "position": {"x": 200, "y": 0},
                    "data": {
                        "id": "condition1",
                        "label": "Check Type",
                        "condition": "input.contains('urgent')"
                    }
                },
                {
                    "id": "person1",
                    "type": "person_job",
                    "position": {"x": 400, "y": -100},
                    "data": {
                        "id": "person1",
                        "label": "Urgent Handler",
                        "personId": "urgent_handler",
                        "prompt": "Handle this urgent request immediately."
                    }
                },
                {
                    "id": "person2",
                    "type": "person_job",
                    "position": {"x": 400, "y": 100},
                    "data": {
                        "id": "person2",
                        "label": "Normal Handler",
                        "personId": "normal_handler",
                        "prompt": "Process this request normally."
                    }
                },
                {
                    "id": "end1",
                    "type": "endpoint",
                    "position": {"x": 600, "y": 0},
                    "data": {"id": "end1", "label": "End"}
                }
            ],
            "arrows": [
                {
                    "id": "arrow-1",
                    "source": "start1",
                    "target": "condition1",
                    "type": "customArrow",
                    "data": {
                        "id": "arrow-data-1",
                        "sourceBlockId": "start1",
                        "targetBlockId": "condition1",
                        "label": "",
                        "contentType": "variable"
                    }
                },
                {
                    "id": "arrow-2",
                    "source": "condition1",
                    "target": "person1",
                    "type": "customArrow",
                    "data": {
                        "id": "arrow-data-2",
                        "sourceBlockId": "condition1",
                        "targetBlockId": "person1",
                        "label": "true",
                        "contentType": "variable"
                    }
                },
                {
                    "id": "arrow-3",
                    "source": "condition1",
                    "target": "person2",
                    "type": "customArrow",
                    "data": {
                        "id": "arrow-data-3",
                        "sourceBlockId": "condition1",
                        "targetBlockId": "person2",
                        "label": "false",
                        "contentType": "variable"
                    }
                },
                {
                    "id": "arrow-4",
                    "source": "person1",
                    "target": "end1",
                    "type": "customArrow",
                    "data": {
                        "id": "arrow-data-4",
                        "sourceBlockId": "person1",
                        "targetBlockId": "end1",
                        "label": "",
                        "contentType": "variable"
                    }
                },
                {
                    "id": "arrow-5",
                    "source": "person2",
                    "target": "end1",
                    "type": "customArrow",
                    "data": {
                        "id": "arrow-data-5",
                        "sourceBlockId": "person2",
                        "targetBlockId": "end1",
                        "label": "",
                        "contentType": "variable"
                    }
                }
            ],
            "persons": [
                {
                    "id": "urgent_handler",
                    "name": "Urgent Handler",
                    "service": "openai",
                    "model": "gpt-4",
                    "apiKeyId": "test-key-1"
                },
                {
                    "id": "normal_handler",
                    "name": "Normal Handler",
                    "service": "openai",
                    "model": "gpt-3.5-turbo",
                    "apiKeyId": "test-key-1"
                }
            ],
            "apiKeys": [
                {
                    "id": "test-key-1",
                    "name": "Test OpenAI Key",
                    "service": "openai"
                }
            ]
        }
    
    @staticmethod
    def iterating_diagram() -> Dict[str, Any]:
        """Diagram with loops and max iterations."""
        return {
            "nodes": [
                {
                    "id": "start1",
                    "type": "start",
                    "position": {"x": 0, "y": 0},
                    "data": {"id": "start1", "label": "Start"}
                },
                {
                    "id": "person1",
                    "type": "person_job",
                    "position": {"x": 200, "y": 0},
                    "data": {
                        "id": "person1",
                        "label": "Processor",
                        "personId": "processor",
                        "prompt": "Process this item and return 'CONTINUE' if more processing needed, 'DONE' if finished.",
                        "maxIterations": 3
                    }
                },
                {
                    "id": "condition1",
                    "type": "condition",
                    "position": {"x": 400, "y": 0},
                    "data": {
                        "id": "condition1",
                        "label": "Check Status",
                        "condition": "output.contains('DONE')"
                    }
                },
                {
                    "id": "end1",
                    "type": "endpoint",
                    "position": {"x": 600, "y": 0},
                    "data": {"id": "end1", "label": "End"}
                }
            ],
            "arrows": [
                {
                    "id": "arrow-1",
                    "source": "start1",
                    "target": "person1",
                    "type": "customArrow",
                    "data": {
                        "id": "arrow-data-1",
                        "sourceBlockId": "start1",
                        "targetBlockId": "person1",
                        "label": "",
                        "contentType": "variable"
                    }
                },
                {
                    "id": "arrow-2",
                    "source": "person1",
                    "target": "condition1",
                    "type": "customArrow",
                    "data": {
                        "id": "arrow-data-2",
                        "sourceBlockId": "person1",
                        "targetBlockId": "condition1",
                        "label": "",
                        "contentType": "variable"
                    }
                },
                {
                    "id": "arrow-3",
                    "source": "condition1",
                    "target": "end1",
                    "type": "customArrow",
                    "data": {
                        "id": "arrow-data-3",
                        "sourceBlockId": "condition1",
                        "targetBlockId": "end1",
                        "label": "true",
                        "contentType": "variable"
                    }
                },
                {
                    "id": "arrow-4",
                    "source": "condition1",
                    "target": "person1",
                    "type": "customArrow",
                    "data": {
                        "id": "arrow-data-4",
                        "sourceBlockId": "condition1",
                        "targetBlockId": "person1",
                        "label": "false",
                        "contentType": "variable"
                    }
                }
            ],
            "persons": [
                {
                    "id": "processor",
                    "name": "Processor",
                    "service": "openai",
                    "model": "gpt-3.5-turbo",
                    "apiKeyId": "test-key-1"
                }
            ],
            "apiKeys": [
                {
                    "id": "test-key-1",
                    "name": "Test OpenAI Key",
                    "service": "openai"
                }
            ]
        }