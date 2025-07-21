#!/usr/bin/env python3
"""
Test the TypeScript AST parser functionality
"""

import sys
import json
from pathlib import Path

# Add the codegen directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'codegen'))

from typescript_parser import parse_typescript, transform_ts_to_python


def test_basic_parsing():
    """Test basic TypeScript parsing"""
    print("=== Test 1: Basic Interface Parsing ===")
    
    source = """
    interface User {
        id: string;
        name: string;
        age?: number;
        isActive: boolean;
    }
    
    type Status = 'active' | 'inactive' | 'pending';
    
    enum Role {
        Admin = 'ADMIN',
        User = 'USER',
        Guest = 'GUEST'
    }
    """
    
    result = parse_typescript({
        'source': source,
        'extractPatterns': ['interface', 'type', 'enum'],
        'includeJSDoc': False
    })
    
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"✅ Parsing successful!")
    print(f"   - Interfaces found: {len(result['interfaces'])}")
    print(f"   - Types found: {len(result['types'])}")
    print(f"   - Enums found: {len(result['enums'])}")
    
    # Display interface details
    for interface in result['interfaces']:
        print(f"\n📋 Interface: {interface['name']}")
        for prop in interface['properties']:
            optional = '?' if prop['optional'] else ''
            print(f"   - {prop['name']}{optional}: {prop['type']}")
    
    # Display type aliases
    for type_alias in result['types']:
        print(f"\n🏷️  Type: {type_alias['name']} = {type_alias['type']}")
    
    # Display enums
    for enum in result['enums']:
        print(f"\n📌 Enum: {enum['name']}")
        for member in enum['members']:
            print(f"   - {member['name']} = {member.get('value', 'auto')}")
    
    return True


def test_jsdoc_parsing():
    """Test JSDoc comment parsing"""
    print("\n\n=== Test 2: JSDoc Comment Parsing ===")
    
    source = """
    /**
     * Represents a user in the system
     * @example
     * const user: User = { id: '123', name: 'John' }
     */
    interface User {
        /** Unique identifier */
        id: string;
        
        /** User's full name */
        name: string;
    }
    """
    
    result = parse_typescript({
        'source': source,
        'extractPatterns': ['interface'],
        'includeJSDoc': True
    })
    
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"✅ JSDoc parsing successful!")
    
    for interface in result['interfaces']:
        print(f"\n📋 Interface: {interface['name']}")
        if interface.get('jsDoc'):
            print(f"   JSDoc: {interface['jsDoc']}")
        for prop in interface['properties']:
            print(f"   - {prop['name']}: {prop['type']}")
            if prop.get('jsDoc'):
                print(f"     JSDoc: {prop['jsDoc']}")
    
    return True


def test_complex_types():
    """Test complex TypeScript types"""
    print("\n\n=== Test 3: Complex Types ===")
    
    source = """
    interface Config<T> {
        data: T;
        metadata: Record<string, any>;
        callbacks: {
            onSuccess: (result: T) => void;
            onError: (error: Error) => Promise<void>;
        };
        items: Array<T>;
        nullable?: T | null;
    }
    
    type AsyncFunction<T, R> = (input: T) => Promise<R>;
    type Tuple = [string, number, boolean];
    """
    
    result = parse_typescript({
        'source': source,
        'extractPatterns': ['interface', 'type']
    })
    
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"✅ Complex type parsing successful!")
    
    # Test TypeScript to Python transformation
    python_result = transform_ts_to_python(result)
    
    print("\n🐍 Python Type Transformations:")
    for py_class in python_result['classes']:
        print(f"\n@dataclass\nclass {py_class['name']}:")
        for field in py_class['fields']:
            print(f"    {field['name']}: {field['type']}")
    
    for py_type in python_result['types']:
        print(f"\n{py_type['name']} = {py_type['type']}")
    
    return True


def test_class_parsing():
    """Test class parsing"""
    print("\n\n=== Test 4: Class Parsing ===")
    
    source = """
    export class DiagramNode {
        private id: string;
        public label: string;
        protected position: { x: number; y: number };
        
        constructor(id: string, label: string) {
            this.id = id;
            this.label = label;
            this.position = { x: 0, y: 0 };
        }
        
        async execute(input: any): Promise<any> {
            return input;
        }
    }
    """
    
    result = parse_typescript({
        'source': source,
        'extractPatterns': ['class']
    })
    
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"✅ Class parsing successful!")
    
    for cls in result.get('classes', []):
        print(f"\n🏗️  Class: {cls['name']}")
        print(f"   Properties:")
        for prop in cls['properties']:
            print(f"   - {prop['name']}: {prop['type']}")
        print(f"   Methods:")
        for method in cls['methods']:
            async_str = 'async ' if method['isAsync'] else ''
            print(f"   - {async_str}{method['name']}(...) → {method['returnType']}")
    
    return True


def main():
    """Run all tests"""
    print("🧪 Testing TypeScript AST Parser\n")
    
    tests = [
        test_basic_parsing,
        test_jsdoc_parsing,
        test_complex_types,
        test_class_parsing
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n\n📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("✨ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())