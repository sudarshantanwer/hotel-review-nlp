#!/usr/bin/env python3
"""
Script to check and validate dependencies used in the project
"""
import ast
import os
from pathlib import Path

def get_imports_from_file(file_path):
    """Extract all imports from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        
        return imports
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return set()

def main():
    """Check all Python files for imports"""
    backend_dir = Path(".")
    all_imports = set()
    
    # Check all Python files in backend
    for py_file in backend_dir.glob("*.py"):
        if py_file.name.startswith('check_'):
            continue
        
        print(f"Checking {py_file.name}...")
        imports = get_imports_from_file(py_file)
        all_imports.update(imports)
        print(f"  Imports: {sorted(imports)}")
    
    print("\n=== ALL THIRD-PARTY IMPORTS ===")
    # Filter out standard library modules
    stdlib_modules = {
        'os', 'sys', 'logging', 'typing', 'datetime', 'json', 'pathlib',
        'ast', 'collections', 'functools', 'itertools', 'operator',
        'tempfile', 'warnings'
    }
    
    third_party = sorted(all_imports - stdlib_modules)
    print(f"Third-party modules found: {third_party}")
    
    # Check against requirements.txt
    try:
        with open('requirements.txt', 'r') as f:
            requirements = [line.strip().split('[')[0] for line in f if line.strip() and not line.startswith('#')]
        
        print(f"\nRequirements in requirements.txt: {sorted(requirements)}")
        
        # Check for unused requirements
        unused = set(requirements) - set(third_party)
        if unused:
            print(f"\n⚠️  Potentially unused requirements: {sorted(unused)}")
        else:
            print("\n✅ All requirements appear to be used!")
            
    except FileNotFoundError:
        print("requirements.txt not found")

if __name__ == "__main__":
    main()
