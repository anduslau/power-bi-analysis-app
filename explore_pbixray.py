#!/usr/bin/env python3
"""
Explore pbixray API.
"""
import sys
sys.path.insert(0, 'src')

import inspect
import pbixray

print("pbixray module members:")
for name in dir(pbixray):
    if not name.startswith('_'):
        print(f"  {name}")

print("\n--- PBIXRay class ---")
if hasattr(pbixray, 'PBIXRay'):
    cls = pbixray.PBIXRay
    print(f"Class: {cls}")
    # Get constructor signature
    try:
        sig = inspect.signature(cls.__init__)
        print(f"__init__ signature: {sig}")
    except:
        pass
    # Get public methods
    methods = []
    for attr_name in dir(cls):
        if not attr_name.startswith('_'):
            methods.append(attr_name)
    print(f"Public methods: {methods}")
    # Print docstring of class
    doc = cls.__doc__
    if doc:
        print(f"Docstring: {doc[:500]}...")

# Check if there are any submodules
print("\n--- Submodules ---")
for name in ['abf', 'core', 'meta', 'utils']:
    if hasattr(pbixray, name):
        module = getattr(pbixray, name)
        print(f"{name}: {module}")