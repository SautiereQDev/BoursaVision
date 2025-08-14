"""
This script modifies the Python path to include the `src` directory located 
within the `backend` folder. This ensures that modules within the `src` 
directory can be imported directly without needing to adjust the import paths 
manually.

Modules added to the Python path:
- `backend/src`

Usage:
- Place this script in the root of the `backend` directory.
- The `src` directory should be a subdirectory of the `backend` folder.

Note:
- The `sys.path.insert` method is used to prepend the `src` directory to the 
    Python path, ensuring it takes precedence over other paths.
"""

import sys
from pathlib import Path

# Ensure backend/src is on Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
