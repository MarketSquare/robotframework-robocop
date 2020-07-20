"""
Reports are configurable summaries after lint scan. For example it could be total number of issues discovered.
They are dynamically loaded during setup according to command line configuration.
"""
from pathlib import Path
from importlib import import_module


def init(linter):
    seen = set()
    for file in Path(__file__).parent.iterdir():
        if file.stem in seen or '__pycache__' in str(file):
            continue
        try:
            if file.is_dir() or (file.suffix in ('.py') and file.stem != '__init__'):
                module = import_module('.' + file.stem, __name__)
                module.register(linter)
                seen.add(file.stem)
        except IOError as error:
            print(error)
