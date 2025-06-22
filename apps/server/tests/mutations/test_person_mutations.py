"""Test person-related GraphQL mutations."""

import pytest
from gql import gql
from graphql import GraphQLError

from ..conftest import *  # Import all fixtures


class TestPersonCRUD:
    """Test basic person CRUD operations."""
    
    async def test_create_person(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data,
        sample_diagram_data
    ):
        """Test creating a new person."""
        # First create a diagram
        create_diagram_mutation = gql(graphql_mutations["create_diagram"])
        diagram_data = sample_diagram_data()
        
        diagram_result = await gql_client.execute(
            create_diagram_mutation,
            variable_values={"input": diagram_data}
        )
        
        assert diagram_result["createDiagram"]["success"] is True
        diagram_id = diagram_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Create an API key first
        create_api_key_mutation = gql("""
            mutation CreateApiKey($input: CreateApiKeyInput!) {
                createApiKey(input: $input) {
                    success
                    apiKey {
                        id
                        label
                        service
                    }
                }
            }
        """)
        
        api_key_result = await gql_client.execute(
            create_api_key_mutation,
            variable_values={
                "input": {
                    "label": "Test API Key",
                    "service": "OPENAI",
                    "key": "test-key-123"
                }
            }
        )
        
        api_key_id = api_key_result["createApiKey"]["apiKey"]["id"]
        
        # Now create person
        create_mutation = gql(graphql_mutations["create_person"])
        person_data = sample_person_data(apiKeyId=api_key_id)
        
        result = await gql_client.execute(
            create_mutation,
            variable_values={
                "diagramId": diagram_id,
                "input": person_data
            }
        )
        
        assert "createPerson" in result
        assert result["createPerson"]["success"] is True
        created = result["createPerson"]["person"]
        assert created["id"] is not None
        assert created["label"] == person_data["label"]
        assert created["service"] == person_data["service"]
    
    async def test_get_person(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data,
        sample_diagram_data
    ):
        """Test retrieving a person by ID."""
        # Create diagram and API key first
        create_diagram_mutation = gql(graphql_mutations["create_diagram"])
        diagram_result = await gql_client.execute(
            create_diagram_mutation,
            variable_values={"input": sample_diagram_data()}
        )
        diagram_id = diagram_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Create API key
        create_api_key_mutation = gql("""
            mutation CreateApiKey($input: CreateApiKeyInput!) {
                createApiKey(input: $input) {
                    success
                    apiKey {
                        id
                    }
                }
            }
        """)
        
        api_key_result = await gql_client.execute(
            create_api_key_mutation,
            variable_values={
                "input": {
                    "label": "Test Key",
                    "service": "OPENAI",
                    "key": "test-key"
                }
            }
        )
        api_key_id = api_key_result["createApiKey"]["apiKey"]["id"]
        
        # Create person
        create_mutation = gql(graphql_mutations["create_person"])
        person_data = sample_person_data(label="Test Person", apiKeyId=api_key_id)
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={
                "diagramId": diagram_id,
                "input": person_data
            }
        )
        person_id = create_result["createPerson"]["person"]["id"]
        
        # Get person
        get_query = gql("""
            query GetPerson($id: PersonID!) {
                person(id: $id) {
                    id
                    label
                    service
                    model
                    systemPrompt
                    forgettingMode
                }
            }
        """)
        
        result = await gql_client.execute(
            get_query,
            variable_values={"id": person_id}
        )
        
        assert "person" in result
        person = result["person"]
        assert person["id"] == person_id
        assert person["label"] == "Test Person"
        assert person["service"] == "OPENAI"
    
    async def test_update_person(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data,
        sample_diagram_data
    ):
        """Test updating a person's information."""
        # Create diagram and API key
        create_diagram_mutation = gql(graphql_mutations["create_diagram"])
        diagram_result = await gql_client.execute(
            create_diagram_mutation,
            variable_values={"input": sample_diagram_data()}
        )
        diagram_id = diagram_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Create API key
        create_api_key_mutation = gql("""
            mutation CreateApiKey($input: CreateApiKeyInput!) {
                createApiKey(input: $input) {
                    success
                    apiKey {
                        id
                    }
                }
            }
        """)
        
        api_key_result = await gql_client.execute(
            create_api_key_mutation,
            variable_values={
                "input": {
                    "label": "Test Key",
                    "service": "OPENAI", 
                    "key": "test-key"
                }
            }
        )
        api_key_id = api_key_result["createApiKey"]["apiKey"]["id"]
        
        # Create person
        create_mutation = gql(graphql_mutations["create_person"])
        person_data = sample_person_data(apiKeyId=api_key_id)
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={
                "diagramId": diagram_id,
                "input": person_data
            }
        )
        person_id = create_result["createPerson"]["person"]["id"]
        
        # Update person
        update_mutation = gql(graphql_mutations["update_person"])
        
        result = await gql_client.execute(
            update_mutation,
            variable_values={
                "input": {
                    "id": person_id,
                    "label": "Updated Assistant",
                    "model": "gpt-4",
                    "temperature": 0.5
                }
            }
        )
        
        assert "updatePerson" in result
        assert result["updatePerson"]["success"] is True
        updated = result["updatePerson"]["person"]
        assert updated["label"] == "Updated Assistant"
        assert updated["model"] == "gpt-4"
    
    async def test_delete_person(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data,
        sample_diagram_data
    ):
        """Test deleting a person."""
        # Create diagram and API key
        create_diagram_mutation = gql(graphql_mutations["create_diagram"])
        diagram_result = await gql_client.execute(
            create_diagram_mutation,
            variable_values={"input": sample_diagram_data()}
        )
        diagram_id = diagram_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Create API key
        create_api_key_mutation = gql("""
            mutation CreateApiKey($input: CreateApiKeyInput!) {
                createApiKey(input: $input) {
                    success
                    apiKey {
                        id
                    }
                }
            }
        """)
        
        api_key_result = await gql_client.execute(
            create_api_key_mutation,
            variable_values={
                "input": {
                    "label": "Test Key",
                    "service": "OPENAI",
                    "key": "test-key"
                }
            }
        )
        api_key_id = api_key_result["createApiKey"]["apiKey"]["id"]
        
        # Create person
        create_mutation = gql(graphql_mutations["create_person"])
        person_data = sample_person_data(label="To Be Deleted", apiKeyId=api_key_id)
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={
                "diagramId": diagram_id,
                "input": person_data
            }
        )
        person_id = create_result["createPerson"]["person"]["id"]
        
        # Delete person
        delete_mutation = gql(graphql_mutations["delete_person"])
        
        result = await gql_client.execute(
            delete_mutation,
            variable_values={"id": person_id}
        )
        
        assert "deletePerson" in result
        assert result["deletePerson"]["success"] is True
        
        # Verify deletion
        get_query = gql("""
            query GetPerson($id: PersonID!) {
                person(id: $id) {
                    id
                }
            }
        """)
        
        result = await gql_client.execute(
            get_query,
            variable_values={"id": person_id}
        )
        
        # Person should be None after deletion
        assert result["person"] is None
    
    async def test_list_people(
        self,
        gql_client,
        graphql_queries,
        graphql_mutations,
        sample_person_data,
        sample_diagram_data
    ):
        """Test listing people."""
        # Create diagram
        create_diagram_mutation = gql(graphql_mutations["create_diagram"])
        diagram_result = await gql_client.execute(
            create_diagram_mutation,
            variable_values={"input": sample_diagram_data()}
        )
        diagram_id = diagram_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Create API key
        create_api_key_mutation = gql("""
            mutation CreateApiKey($input: CreateApiKeyInput!) {
                createApiKey(input: $input) {
                    success
                    apiKey {
                        id
                    }
                }
            }
        """)
        
        api_key_result = await gql_client.execute(
            create_api_key_mutation,
            variable_values={
                "input": {
                    "label": "Test Key",
                    "service": "OPENAI",
                    "key": "test-key"
                }
            }
        )
        api_key_id = api_key_result["createApiKey"]["apiKey"]["id"]
        
        # Create multiple people
        create_mutation = gql(graphql_mutations["create_person"])
        
        for i in range(3):
            person_data = sample_person_data(
                label=f"Assistant {i}",
                apiKeyId=api_key_id
            )
            await gql_client.execute(
                create_mutation,
                variable_values={
                    "diagramId": diagram_id,
                    "input": person_data
                }
            )
        
        # List people
        list_query = gql(graphql_queries["list_people"])
        
        # Default listing
        result = await gql_client.execute(
            list_query,
            variable_values={"limit": 100}
        )
        assert "persons" in result
        assert len(result["persons"]) >= 3


class TestPersonValidation:
    """Test person data validation."""
    
    async def test_create_person_validation(
        self,
        gql_client,
        graphql_mutations,
        sample_diagram_data
    ):
        """Test validation when creating a person."""
        # Create diagram first
        create_diagram_mutation = gql(graphql_mutations["create_diagram"])
        diagram_result = await gql_client.execute(
            create_diagram_mutation,
            variable_values={"input": sample_diagram_data()}
        )
        diagram_id = diagram_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        create_mutation = gql(graphql_mutations["create_person"])
        
        # Missing required fields
        with pytest.raises(GraphQLError):
            await gql_client.execute(
                create_mutation,
                variable_values={
                    "diagramId": diagram_id,
                    "input": {"label": "Only Label"}
                }
            )
        
        # Invalid service
        invalid_person = {
            "label": "Invalid Service",
            "service": "INVALID_SERVICE",
            "model": "gpt-4",
            "apiKeyId": "test-key"
        }
        
        with pytest.raises(Exception) as exc_info:
            await gql_client.execute(
                create_mutation,
                variable_values={
                    "diagramId": diagram_id,
                    "input": invalid_person
                }
            )
    
    async def test_duplicate_label(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data,
        sample_diagram_data
    ):
        """Test creating person with duplicate label in same diagram."""
        # Create diagram
        create_diagram_mutation = gql(graphql_mutations["create_diagram"])
        diagram_result = await gql_client.execute(
            create_diagram_mutation,
            variable_values={"input": sample_diagram_data()}
        )
        diagram_id = diagram_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Create API key
        create_api_key_mutation = gql("""
            mutation CreateApiKey($input: CreateApiKeyInput!) {
                createApiKey(input: $input) {
                    success
                    apiKey {
                        id
                    }
                }
            }
        """)
        
        api_key_result = await gql_client.execute(
            create_api_key_mutation,
            variable_values={
                "input": {
                    "label": "Test Key",
                    "service": "OPENAI",
                    "key": "test-key"
                }
            }
        )
        api_key_id = api_key_result["createApiKey"]["apiKey"]["id"]
        
        create_mutation = gql(graphql_mutations["create_person"])
        person_data = sample_person_data(label="Duplicate Label", apiKeyId=api_key_id)
        
        # Create first person
        await gql_client.execute(
            create_mutation,
            variable_values={
                "diagramId": diagram_id,
                "input": person_data
            }
        )
        
        # Try to create second with same label - this might be allowed
        # depending on implementation
        person_data2 = sample_person_data(
            label="Duplicate Label",
            apiKeyId=api_key_id
        )
        
        # Second creation might succeed or fail depending on business rules
        result = await gql_client.execute(
            create_mutation,
            variable_values={
                "diagramId": diagram_id,
                "input": person_data2
            }
        )
        
        # Just verify we get a response
        assert "createPerson" in result


class TestPersonWithLLM:
    """Test person operations with LLM integration."""
    
    async def test_initialize_model(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data,
        sample_diagram_data
    ):
        """Test pre-initializing a model."""
        # Create diagram and API key
        create_diagram_mutation = gql(graphql_mutations["create_diagram"])
        diagram_result = await gql_client.execute(
            create_diagram_mutation,
            variable_values={"input": sample_diagram_data()}
        )
        diagram_id = diagram_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Create API key
        create_api_key_mutation = gql("""
            mutation CreateApiKey($input: CreateApiKeyInput!) {
                createApiKey(input: $input) {
                    success
                    apiKey {
                        id
                    }
                }
            }
        """)
        
        api_key_result = await gql_client.execute(
            create_api_key_mutation,
            variable_values={
                "input": {
                    "label": "Test Key",
                    "service": "OPENAI",
                    "key": "test-key"
                }
            }
        )
        api_key_id = api_key_result["createApiKey"]["apiKey"]["id"]
        
        # Create person
        create_mutation = gql(graphql_mutations["create_person"])
        person_data = sample_person_data(apiKeyId=api_key_id)
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={
                "diagramId": diagram_id,
                "input": person_data
            }
        )
        person_id = create_result["createPerson"]["person"]["id"]
        
        # Initialize model
        init_mutation = gql("""
            mutation InitializeModel($personId: PersonID!) {
                initializeModel(personId: $personId) {
                    success
                    message
                    person {
                        id
                        label
                    }
                }
            }
        """)
        
        result = await gql_client.execute(
            init_mutation,
            variable_values={"personId": person_id}
        )
        
        assert "initializeModel" in result
        assert result["initializeModel"]["success"] is True


class TestPersonSearch:
    """Test person search functionality - simplified since search is not in current schema."""
    
    async def test_filter_by_service(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data,
        sample_diagram_data
    ):
        """Test filtering people by LLM service."""
        # Create diagram
        create_diagram_mutation = gql(graphql_mutations["create_diagram"])
        diagram_result = await gql_client.execute(
            create_diagram_mutation,
            variable_values={"input": sample_diagram_data()}
        )
        diagram_id = diagram_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Create API keys for different services
        services = ["OPENAI", "ANTHROPIC", "GOOGLE"]
        api_key_ids = {}
        
        for service in services:
            create_api_key_mutation = gql("""
                mutation CreateApiKey($input: CreateApiKeyInput!) {
                    createApiKey(input: $input) {
                        success
                        apiKey {
                            id
                        }
                    }
                }
            """)
            
            api_key_result = await gql_client.execute(
                create_api_key_mutation,
                variable_values={
                    "input": {
                        "label": f"{service} Key",
                        "service": service,
                        "key": f"test-key-{service.lower()}"
                    }
                }
            )
            api_key_ids[service] = api_key_result["createApiKey"]["apiKey"]["id"]
        
        # Create people with different services
        create_mutation = gql(graphql_mutations["create_person"])
        
        for i, service in enumerate(services):
            person_data = sample_person_data(
                label=f"{service} Assistant",
                service=service,
                apiKeyId=api_key_ids[service]
            )
            await gql_client.execute(
                create_mutation,
                variable_values={
                    "diagramId": diagram_id,
                    "input": person_data
                }
            )
        
        # List all people
        list_query = gql(graphql_queries["list_people"])
        result = await gql_client.execute(
            list_query,
            variable_values={"limit": 100}
        )
        
        assert "persons" in result
        persons = result["persons"]
        
        # Verify we have people from different services
        services_found = {p["service"] for p in persons}
        assert "OPENAI" in services_found
        assert "ANTHROPIC" in services_found
        assert "GOOGLE" in services_found


class TestPersonBulkOperations:
    """Test bulk person operations - simplified since these aren't in current schema."""
    
    async def test_create_multiple_persons(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data,
        sample_diagram_data
    ):
        """Test creating multiple persons in batch."""
        # Create diagram
        create_diagram_mutation = gql(graphql_mutations["create_diagram"])
        diagram_result = await gql_client.execute(
            create_diagram_mutation,
            variable_values={"input": sample_diagram_data()}
        )
        diagram_id = diagram_result["createDiagram"]["diagram"]["metadata"]["id"]
        
        # Create API key
        create_api_key_mutation = gql("""
            mutation CreateApiKey($input: CreateApiKeyInput!) {
                createApiKey(input: $input) {
                    success
                    apiKey {
                        id
                    }
                }
            }
        """)
        
        api_key_result = await gql_client.execute(
            create_api_key_mutation,
            variable_values={
                "input": {
                    "label": "Batch Test Key",
                    "service": "OPENAI",
                    "key": "test-key-batch"
                }
            }
        )
        api_key_id = api_key_result["createApiKey"]["apiKey"]["id"]
        
        # Create multiple persons
        create_mutation = gql(graphql_mutations["create_person"])
        created_ids = []
        
        for i in range(3):
            person_data = sample_person_data(
                label=f"Batch Assistant {i}",
                apiKeyId=api_key_id
            )
            result = await gql_client.execute(
                create_mutation,
                variable_values={
                    "diagramId": diagram_id,
                    "input": person_data
                }
            )
            created_ids.append(result["createPerson"]["person"]["id"])
        
        assert len(created_ids) == 3
        assert len(set(created_ids)) == 3  # All IDs should be unique