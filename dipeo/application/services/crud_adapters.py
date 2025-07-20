"""CRUD adapters to provide standard interfaces for domain services."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar('T')


class CrudAdapter(ABC, Generic[T]):
    """Base adapter providing standard CRUD interface."""
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> T:
        """Create a new entity."""
        pass
    
    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """Get entity by ID."""
        pass
    
    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> T:
        """Update existing entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete entity by ID."""
        pass
    
    @abstractmethod
    async def list(self, **filters) -> List[T]:
        """List entities with optional filters."""
        pass


class ApiKeyCrudAdapter(CrudAdapter[Dict[str, Any]]):
    """Adapter for APIKeyService to provide standard CRUD interface."""
    
    def __init__(self, api_key_service):
        self.service = api_key_service
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new API key."""
        return await self.service.create_api_key(
            label=data['label'],
            service=data['service'],
            key=data['key']
        )
    
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get API key by ID."""
        return await self.service.get_api_key(id)
    
    async def update(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing API key."""
        return await self.service.update_api_key(
            key_id=id,
            label=data.get('label'),
            service=data.get('service'),
            key=data.get('key')
        )
    
    async def delete(self, id: str) -> bool:
        """Delete API key by ID."""
        await self.service.delete_api_key(id)
        return True
    
    async def list(self, **filters) -> List[Dict[str, Any]]:
        """List all API keys."""
        return await self.service.list_api_keys()


class DiagramCrudAdapter(CrudAdapter[Dict[str, Any]]):
    """Adapter for integrated diagram service operations."""
    
    def __init__(self, integrated_diagram_service, diagram_storage_service):
        self.integrated_service = integrated_diagram_service
        self.storage_service = diagram_storage_service
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new diagram."""
        # For now, diagrams are created through save_diagram
        diagram = data  # Assume data is already a diagram dict
        await self.storage_service.save_diagram(
            diagram_id=diagram['id'],
            diagram=diagram,
            format_type=data.get('format', 'native')
        )
        return diagram
    
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get diagram by ID."""
        try:
            return await self.integrated_service.get_diagram(id)
        except:
            return None
    
    async def update(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing diagram."""
        # Get existing diagram
        diagram = await self.get(id)
        if not diagram:
            raise ValueError(f"Diagram {id} not found")
        
        # Update fields
        diagram.update(data)
        
        # Save updated diagram
        await self.storage_service.save_diagram(
            diagram_id=id,
            diagram=diagram,
            format_type=diagram.get('format', 'native')
        )
        return diagram
    
    async def delete(self, id: str) -> bool:
        """Delete diagram by ID."""
        # Would need to implement delete in storage service
        # For now, return False
        return False
    
    async def list(self, **filters) -> List[Dict[str, Any]]:
        """List all diagrams."""
        return await self.integrated_service.list_diagrams()


class PersonCrudAdapter(CrudAdapter[Dict[str, Any]]):
    """Adapter for Person entities within diagrams."""
    
    def __init__(self, integrated_diagram_service, diagram_storage_service):
        self.integrated_service = integrated_diagram_service
        self.storage_service = diagram_storage_service
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new person within a diagram."""
        diagram_id = data.pop('diagram_id')
        diagram = await self.integrated_service.get_diagram(diagram_id)
        if not diagram:
            raise ValueError(f"Diagram {diagram_id} not found")
        
        # Add person to diagram
        if 'persons' not in diagram:
            diagram['persons'] = []
        
        person = {
            'id': data['id'],
            'name': data['name'],
            'role': data.get('role', ''),
            'description': data.get('description', ''),
            'llm_service': data.get('llm_service', 'openai'),
            'llm_model': data.get('llm_model', 'gpt-4.1-nano')
        }
        diagram['persons'].append(person)
        
        # Save updated diagram
        await self.storage_service.save_diagram(
            diagram_id=diagram_id,
            diagram=diagram,
            format_type=diagram.get('format', 'native')
        )
        
        return person
    
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get person by ID (requires searching through diagrams)."""
        # This is inefficient but works for now
        diagrams = await self.integrated_service.list_diagrams()
        for diagram in diagrams:
            if 'persons' in diagram:
                for person in diagram['persons']:
                    if person['id'] == id:
                        return person
        return None
    
    async def update(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing person."""
        # Find the diagram containing this person
        diagrams = await self.integrated_service.list_diagrams()
        for diagram in diagrams:
            if 'persons' in diagram:
                for i, person in enumerate(diagram['persons']):
                    if person['id'] == id:
                        # Update person
                        person.update(data)
                        diagram['persons'][i] = person
                        
                        # Save diagram
                        await self.storage_service.save_diagram(
                            diagram_id=diagram['id'],
                            diagram=diagram,
                            format_type=diagram.get('format', 'native')
                        )
                        return person
        
        raise ValueError(f"Person {id} not found")
    
    async def delete(self, id: str) -> bool:
        """Delete person by ID."""
        # Find and remove from diagram
        diagrams = await self.integrated_service.list_diagrams()
        for diagram in diagrams:
            if 'persons' in diagram:
                original_len = len(diagram['persons'])
                diagram['persons'] = [p for p in diagram['persons'] if p['id'] != id]
                if len(diagram['persons']) < original_len:
                    # Person was removed, save diagram
                    await self.storage_service.save_diagram(
                        diagram_id=diagram['id'],
                        diagram=diagram,
                        format_type=diagram.get('format', 'native')
                    )
                    return True
        return False
    
    async def list(self, **filters) -> List[Dict[str, Any]]:
        """List all persons across diagrams."""
        persons = []
        diagrams = await self.integrated_service.list_diagrams()
        for diagram in diagrams:
            if 'persons' in diagram:
                persons.extend(diagram['persons'])
        return persons


# Note: Node, Arrow, and Handle entities are part of diagrams
# and are edited through diagram mutations, not as separate entities


class ExecutionCrudAdapter(CrudAdapter[Dict[str, Any]]):
    """Adapter for Execution entities."""
    
    def __init__(self, execution_state_store):
        self.state_store = execution_state_store
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new execution."""
        # Executions are created through the execution engine
        # This is a placeholder for GraphQL mutation support
        execution_id = data['id']
        state = {
            'id': execution_id,
            'status': 'pending',
            'diagram_id': data.get('diagram_id'),
            'started_at': None,
            'completed_at': None,
            'node_states': {},
            'outputs': {}
        }
        await self.state_store.save_state(execution_id, state)
        return state
    
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """Get execution by ID."""
        return await self.state_store.get_state(id)
    
    async def update(self, id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing execution."""
        state = await self.get(id)
        if not state:
            raise ValueError(f"Execution {id} not found")
        
        state.update(data)
        await self.state_store.save_state(id, state)
        return state
    
    async def delete(self, id: str) -> bool:
        """Delete execution by ID."""
        # Would need to implement delete in state store
        return False
    
    async def list(self, **filters) -> List[Dict[str, Any]]:
        """List all executions."""
        # Would need to implement list in state store
        return []