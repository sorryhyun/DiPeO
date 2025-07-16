"""Test if dependency_injector can be imported correctly."""
import sys

print("=== Testing dependency_injector imports ===")

try:
    import dependency_injector
    print("[OK] dependency_injector imported successfully")
    
    # Test specific submodules that cause issues
    from dependency_injector import providers
    print("[OK] dependency_injector.providers imported")
    
    from dependency_injector import errors
    print("[OK] dependency_injector.errors imported")
    
    from dependency_injector import containers
    print("[OK] dependency_injector.containers imported")
    
    from dependency_injector import wiring
    print("[OK] dependency_injector.wiring imported")
    
    # Try to create a simple container
    class TestContainer(containers.DeclarativeContainer):
        test_provider = providers.Singleton(str, "test")
    
    container = TestContainer()
    print("[OK] Created test container successfully")
    
    print("\nAll imports successful!")
    sys.exit(0)
    
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    sys.exit(1)