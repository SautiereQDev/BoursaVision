import sys
from pathlib import Path

# Ensure backend/src is on Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
