"""
Conftest for market API tests.
Simplified configuration without complex infrastructure dependencies.
"""

import pytest
import sys
from pathlib import Path

# Add src to Python path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir / "src"))
