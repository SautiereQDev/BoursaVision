import os
import sys

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles

# Add backend root to PYTHONPATH for tests so that 'src' package is found
tests_dir = os.path.dirname(__file__)
backend_dir = os.path.abspath(os.path.join(tests_dir, ".."))
sys.path.insert(0, backend_dir)


@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kwargs):
    return "TEXT"
