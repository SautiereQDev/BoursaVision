#!/usr/bin/env python3
"""Fix abstract method implementations in domain base test file."""

import re

def fix_abstract_classes():
    """Fix abstract method implementations in test classes."""
    
    file_path = "tests/unit/domain/entities/test_domain_base.py"
    
    with open(file_path) as f:
        content = f.read()
    
    # Classes that need __eq__ method
    classes_to_fix = [
        r"class ConcreteAggregate\(AggregateRoot\):",
        r"class ConcreteEntity\(Entity\):",
        r"class TestAggregate\(AggregateRoot\):",
        r"class MyTestEntity\(Entity\):",
        r"class MyTestAggregate\(AggregateRoot\):",
    ]
    
    for class_pattern in classes_to_fix:
        # Find the class and add __eq__ method if not present
        class_matches = list(re.finditer(class_pattern, content))
        
        for match in reversed(class_matches):  # Process from end to avoid offset issues
            class_start = match.end()
            
            # Find the next method or end of class
            next_def_match = re.search(r'\n\s{8,}def ', content[class_start:])
            if next_def_match:
                insert_pos = class_start + next_def_match.start()
                # Check if __eq__ already exists
                class_block = content[class_start:insert_pos]
                if "__eq__" not in class_block:
                    # Add __eq__ method
                    eq_method = "\n            def __eq__(self, other: object) -> bool:\n                return isinstance(other, type(self))\n"
                    content = content[:insert_pos] + eq_method + content[insert_pos:]
            else:
                # End of file or class, find the pass statement or other content
                rest_content = content[class_start:]
                if "__eq__" not in rest_content[:200]:  # Check first 200 chars
                    eq_method = "\n            def __eq__(self, other: object) -> bool:\n                return isinstance(other, type(self))\n"
                    # Find the end of the line
                    newline_pos = content.find('\n', class_start)
                    if newline_pos != -1:
                        content = content[:newline_pos] + eq_method + content[newline_pos:]
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("Fixed abstract method implementations")

if __name__ == "__main__":
    fix_abstract_classes()
