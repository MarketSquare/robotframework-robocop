import contextlib
import os
from pathlib import Path

TEST_DATA_LINTER_DIR = Path(__file__).parent / "linter" / "test_data"


@contextlib.contextmanager
def working_directory(path: Path):
    """Change working directory and return to previous on exit"""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)
