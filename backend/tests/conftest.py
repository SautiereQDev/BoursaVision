import os
import sys

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles

# Add backend/src to PYTHONPATH for tests
tests_dir = os.path.dirname(__file__)
backend_dir = os.path.abspath(os.path.join(tests_dir, ".."))
# 'src' folder contains the 'src' package
sys.path.insert(0, os.path.join(backend_dir, "src"))

# Assure that the src/ folder is at the top of PYTHONPATH for all tests
if os.path.join(backend_dir, "src") not in sys.path:
    sys.path.insert(0, os.path.join(backend_dir, "src"))


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kwargs):
    return "TEXT"
