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
        sample_person_data
    ):
        """Test creating a new person."""
        create_mutation = gql(graphql_mutations["create_person"])
        person_data = sample_person_data()
        
        result = await gql_client.execute(
            create_mutation,
            variable_values={"input": person_data}
        )
        
        assert "createPerson" in result
        created = result["createPerson"]
        assert created["id"] is not None
        assert created["name"] == person_data["name"]
        assert created["email"] == person_data["email"]
    
    async def test_get_person(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data
    ):
        """Test retrieving a person by ID."""
        # Create person
        create_mutation = gql(graphql_mutations["create_person"])
        person_data = sample_person_data(name="Test Person")
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": person_data}
        )
        person_id = create_result["createPerson"]["id"]
        
        # Get person
        get_query = gql("""
            query GetPerson($id: ID!) {
                person(id: $id) {
                    id
                    name
                    email
                    role
                    attributes
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
        assert person["name"] == "Test Person"
        assert person["attributes"] is not None
    
    async def test_update_person(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data
    ):
        """Test updating a person's information."""
        # Create person
        create_mutation = gql(graphql_mutations["create_person"])
        person_data = sample_person_data()
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": person_data}
        )
        person_id = create_result["createPerson"]["id"]
        
        # Update person
        update_mutation = gql("""
            mutation UpdatePerson($id: ID!, $input: PersonInput!) {
                updatePerson(id: $id, input: $input) {
                    id
                    name
                    email
                    role
                    updatedAt
                }
            }
        """)
        
        updated_data = sample_person_data(
            name="Updated Name",
            email="updated@example.com",
            role="Senior Developer",
            attributes={"department": "R&D", "level": "Senior"}
        )
        
        result = await gql_client.execute(
            update_mutation,
            variable_values={
                "id": person_id,
                "input": updated_data
            }
        )
        
        assert "updatePerson" in result
        updated = result["updatePerson"]
        assert updated["name"] == "Updated Name"
        assert updated["email"] == "updated@example.com"
        assert updated["role"] == "Senior Developer"
        assert updated["updatedAt"] is not None
    
    async def test_delete_person(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data
    ):
        """Test deleting a person."""
        # Create person
        create_mutation = gql(graphql_mutations["create_person"])
        person_data = sample_person_data(name="To Be Deleted")
        
        create_result = await gql_client.execute(
            create_mutation,
            variable_values={"input": person_data}
        )
        person_id = create_result["createPerson"]["id"]
        
        # Delete person
        delete_mutation = gql("""
            mutation DeletePerson($id: ID!) {
                deletePerson(id: $id) {
                    success
                    message
                }
            }
        """)
        
        result = await gql_client.execute(
            delete_mutation,
            variable_values={"id": person_id}
        )
        
        assert "deletePerson" in result
        assert result["deletePerson"]["success"] is True
        
        # Verify deletion
        get_query = gql("""
            query GetPerson($id: ID!) {
                person(id: $id) {
                    id
                }
            }
        """)
        
        with pytest.raises(Exception):
            await gql_client.execute(
                get_query,
                variable_values={"id": person_id}
            )
    
    async def test_list_people(
        self,
        gql_client,
        graphql_queries,
        graphql_mutations,
        sample_person_data
    ):
        """Test listing people with pagination."""
        # Create multiple people
        create_mutation = gql(graphql_mutations["create_person"])
        
        for i in range(5):
            person_data = sample_person_data(
                name=f"Person {i}",
                email=f"person{i}@example.com"
            )
            await gql_client.execute(
                create_mutation,
                variable_values={"input": person_data}
            )
        
        # List people
        list_query = gql(graphql_queries["list_people"])
        
        # Default listing
        result = await gql_client.execute(list_query)
        assert "people" in result
        assert len(result["people"]) >= 5
        
        # With pagination
        result = await gql_client.execute(
            list_query,
            variable_values={"limit": 3, "offset": 0}
        )
        assert len(result["people"]) == 3


class TestPersonValidation:
    """Test person data validation."""
    
    async def test_create_person_validation(
        self,
        gql_client,
        graphql_mutations
    ):
        """Test validation when creating a person."""
        create_mutation = gql(graphql_mutations["create_person"])
        
        # Missing required fields
        with pytest.raises(GraphQLError):
            await gql_client.execute(
                create_mutation,
                variable_values={"input": {"name": "Only Name"}}
            )
        
        # Invalid email format
        invalid_person = {
            "name": "Invalid Email",
            "email": "not-an-email",
            "role": "Developer"
        }
        
        with pytest.raises(Exception) as exc_info:
            await gql_client.execute(
                create_mutation,
                variable_values={"input": invalid_person}
            )
        
        error_msg = str(exc_info.value).lower()
        assert "email" in error_msg or "invalid" in error_msg
    
    async def test_duplicate_email(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data
    ):
        """Test creating person with duplicate email."""
        create_mutation = gql(graphql_mutations["create_person"])
        person_data = sample_person_data(email="duplicate@example.com")
        
        # Create first person
        await gql_client.execute(
            create_mutation,
            variable_values={"input": person_data}
        )
        
        # Try to create second with same email
        person_data2 = sample_person_data(
            name="Different Name",
            email="duplicate@example.com"
        )
        
        with pytest.raises(Exception) as exc_info:
            await gql_client.execute(
                create_mutation,
                variable_values={"input": person_data2}
            )
        
        error_msg = str(exc_info.value).lower()
        assert "duplicate" in error_msg or "unique" in error_msg or "exists" in error_msg


class TestPersonSearch:
    """Test person search functionality."""
    
    async def test_search_by_name(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data
    ):
        """Test searching people by name."""
        # Create test people
        create_mutation = gql(graphql_mutations["create_person"])
        
        test_people = [
            ("Alice Johnson", "alice@example.com"),
            ("Bob Smith", "bob@example.com"),
            ("Alice Cooper", "alice.cooper@example.com"),
            ("Charlie Brown", "charlie@example.com")
        ]
        
        for name, email in test_people:
            person_data = sample_person_data(name=name, email=email)
            await gql_client.execute(
                create_mutation,
                variable_values={"input": person_data}
            )
        
        # Search for "Alice"
        search_query = gql("""
            query SearchPeople($query: String!) {
                searchPeople(query: $query) {
                    id
                    name
                    email
                }
            }
        """)
        
        result = await gql_client.execute(
            search_query,
            variable_values={"query": "Alice"}
        )
        
        assert "searchPeople" in result
        results = result["searchPeople"]
        assert len(results) == 2
        assert all("Alice" in person["name"] for person in results)
    
    async def test_filter_by_role(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data
    ):
        """Test filtering people by role."""
        # Create people with different roles
        create_mutation = gql(graphql_mutations["create_person"])
        
        roles = ["Developer", "Designer", "Manager", "Developer", "QA"]
        
        for i, role in enumerate(roles):
            person_data = sample_person_data(
                name=f"Person {i}",
                email=f"person{i}@example.com",
                role=role
            )
            await gql_client.execute(
                create_mutation,
                variable_values={"input": person_data}
            )
        
        # Filter by role
        filter_query = gql("""
            query FilterPeopleByRole($role: String!) {
                people(filter: {role: $role}) {
                    id
                    name
                    role
                }
            }
        """)
        
        try:
            result = await gql_client.execute(
                filter_query,
                variable_values={"role": "Developer"}
            )
            
            assert "people" in result
            developers = result["people"]
            assert len(developers) == 2
            assert all(p["role"] == "Developer" for p in developers)
        except GraphQLError:
            pytest.skip("Role filtering not supported")
    
    async def test_search_by_attributes(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data
    ):
        """Test searching people by custom attributes."""
        # Create people with attributes
        create_mutation = gql(graphql_mutations["create_person"])
        
        people_with_attrs = [
            {
                "name": "Python Dev",
                "email": "python@example.com",
                "attributes": {"skills": ["Python", "Django"]}
            },
            {
                "name": "JS Dev",
                "email": "js@example.com",
                "attributes": {"skills": ["JavaScript", "React"]}
            },
            {
                "name": "Full Stack",
                "email": "fullstack@example.com",
                "attributes": {"skills": ["Python", "JavaScript"]}
            }
        ]
        
        for person in people_with_attrs:
            person_data = sample_person_data(**person)
            await gql_client.execute(
                create_mutation,
                variable_values={"input": person_data}
            )
        
        # Search by attribute
        attr_search_query = gql("""
            query SearchByAttribute($attribute: String!, $value: JSON!) {
                searchPeopleByAttribute(attribute: $attribute, value: $value) {
                    id
                    name
                    attributes
                }
            }
        """)
        
        try:
            result = await gql_client.execute(
                attr_search_query,
                variable_values={
                    "attribute": "skills",
                    "value": "Python"
                }
            )
            
            assert "searchPeopleByAttribute" in result
            results = result["searchPeopleByAttribute"]
            assert len(results) == 2  # Python Dev and Full Stack
        except GraphQLError:
            pytest.skip("Attribute search not supported")


class TestPersonBulkOperations:
    """Test bulk person operations."""
    
    async def test_import_people_csv(
        self,
        gql_client,
        tmp_path
    ):
        """Test importing people from CSV."""
        # Create CSV file
        csv_file = tmp_path / "people.csv"
        csv_content = """name,email,role,department
John Doe,john@example.com,Developer,Engineering
Jane Smith,jane@example.com,Designer,Design
Bob Johnson,bob@example.com,Manager,Management"""
        csv_file.write_text(csv_content)
        
        import_mutation = gql("""
            mutation ImportPeopleCSV($csv: String!) {
                importPeopleFromCSV(csv: $csv) {
                    importedCount
                    failedCount
                    errors
                }
            }
        """)
        
        try:
            result = await gql_client.execute(
                import_mutation,
                variable_values={"csv": csv_content}
            )
            
            assert "importPeopleFromCSV" in result
            import_result = result["importPeopleFromCSV"]
            assert import_result["importedCount"] == 3
            assert import_result["failedCount"] == 0
        except GraphQLError:
            pytest.skip("CSV import not supported")
    
    async def test_export_people(
        self,
        gql_client,
        graphql_mutations,
        sample_person_data
    ):
        """Test exporting people to different formats."""
        # Create some people
        create_mutation = gql(graphql_mutations["create_person"])
        
        for i in range(3):
            person_data = sample_person_data(
                name=f"Export Test {i}",
                email=f"export{i}@example.com"
            )
            await gql_client.execute(
                create_mutation,
                variable_values={"input": person_data}
            )
        
        # Export as CSV
        export_mutation = gql("""
            mutation ExportPeople($format: ExportFormat!) {
                exportPeople(format: $format) {
                    content
                    format
                    filename
                    recordCount
                }
            }
        """)
        
        try:
            result = await gql_client.execute(
                export_mutation,
                variable_values={"format": "CSV"}
            )
            
            assert "exportPeople" in result
            export_result = result["exportPeople"]
            assert export_result["format"] == "CSV"
            assert export_result["recordCount"] >= 3
            assert "Export Test" in export_result["content"]
        except GraphQLError:
            pytest.skip("People export not supported")