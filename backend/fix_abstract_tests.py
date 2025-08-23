#!/usr/bin/env python3
"""Script to fix abstract method implementations in test files."""

import re
import os

def fix_concrete_aggregate(file_path):
    """Fix ConcreteAggregate classes to implement abstract methods."""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to find ConcreteAggregate class definitions
    pattern = r'(class ConcreteAggregate\(AggregateRoot\):\s*)([\s\S]*?)(?=\n\s{0,8}[a-zA-Z_]|\n\n|\Z)'
    
    def replace_class(match):
        class_def = match.group(1)
        class_body = match.group(2)
        
        # Check if __eq__ is already implemented
        if '__eq__' in class_body:
            return match.group(0)  # No change needed
        
        # Add __eq__ method
        new_body = f"""
            def __eq__(self, other: object) -> bool:
                return isinstance(other, ConcreteAggregate)
{class_body}"""
        
        return class_def + new_body
    
    # Apply the fix
    fixed_content = re.sub(pattern, replace_class, content, flags=re.MULTILINE)
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(fixed_content)
    
    print(f"Fixed {file_path}")

# Fix the test file
fix_concrete_aggregate("/home/quentin-sautiere/Documents/workspace/python/boursa-vision/backend/tests/unit/domain/entities/test_domain_base.py")
