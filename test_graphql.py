#!/usr/bin/env python3
"""Test GraphQL endpoint availability."""
import requests
import time
import sys

def test_graphql():
    """Test if GraphQL endpoint is available."""
    url = "http://localhost:8000/graphql"
    
    # GraphQL introspection query
    query = """
    query {
        __schema {
            types {
                name
            }
        }
    }
    """
    
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.post(
                url,
                json={"query": query},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ GraphQL endpoint is working!")
                print(f"Found {len(data['data']['__schema']['types'])} types")
                return True
            else:
                print(f"❌ GraphQL returned status {response.status_code}")
                print(response.text)
                return False
                
        except requests.exceptions.ConnectionError:
            if i < max_retries - 1:
                print(f"⏳ Waiting for server to start... ({i+1}/{max_retries})")
                time.sleep(2)
            else:
                print("❌ Could not connect to GraphQL endpoint")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    return False

if __name__ == "__main__":
    success = test_graphql()
    sys.exit(0 if success else 1)