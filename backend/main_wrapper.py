#!/usr/bin/env python3
"""
Wrapper script to maintain backward compatibility.
This file provides the same interface as the old main.py
"""

import sys
from pathlib import Path

# Add src to path for imports
backend_dir = Path(__file__).parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

# Import and run the new main
from boursa_vision.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_wrapper:app",
        host="0.0.0.0", 
        port=8000,
        reload=True
    )
