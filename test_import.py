#!/usr/bin/env python3
"""
Test Import Script

This script attempts to import all test modules to verify that they can be loaded
without errors. This helps identify issues with test discovery.
"""

import os
import sys
import importlib
import traceback
from pathlib import Path

def check_test_file(file_path):
    """Check if a test file can be imported without errors"""
    try:
        # Convert file path to module path
        module_path = str(file_path).replace('/', '.').replace('\\', '.')
        module_path = module_path.replace('.py', '')
        
        # Import the module
        module = importlib.import_module(module_path)
        
        # Check if it has test functions
        has_test_functions = False
        for name in dir(module):
            if name.startswith('test_'):
                has_test_functions = True
                break
        
        return True, has_test_functions, None
    except Exception as e:
        return False, False, str(e)

def main():
    """Main function"""
    print("Checking test files...")
    
    # Find all test files
    test_files = []
    for root, _, files in os.walk('tests'):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                test_files.append(Path(root) / file)
    
    print(f"Found {len(test_files)} test files")
    
    # Check each test file
    results = {
        'success': [],
        'no_test_functions': [],
        'error': []
    }
    
    for file_path in test_files:
        print(f"Checking {file_path}...")
        success, has_test_functions, error = check_test_file(file_path)
        
        if success:
            if has_test_functions:
                results['success'].append(str(file_path))
            else:
                results['no_test_functions'].append(str(file_path))
        else:
            results['error'].append((str(file_path), error))
    
    # Print results
    print("\nResults:")
    print(f"- {len(results['success'])} files imported successfully and contain test functions")
    print(f"- {len(results['no_test_functions'])} files imported successfully but don't contain test functions")
    print(f"- {len(results['error'])} files failed to import")
    
    if results['no_test_functions']:
        print("\nFiles without test functions:")
        for file in results['no_test_functions']:
            print(f"- {file}")
    
    if results['error']:
        print("\nFiles with import errors:")
        for file, error in results['error']:
            print(f"- {file}: {error}")
    
    return 0 if not results['error'] else 1

if __name__ == "__main__":
    sys.exit(main())