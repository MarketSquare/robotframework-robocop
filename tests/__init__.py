import contextlib
import os
from pathlib import Path


@contextlib.contextmanager
def working_directory(path: Path):
    """Change working directory and return to previous on exit"""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)
