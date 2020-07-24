from pathlib import Path
from importlib import import_module


def modules_in_current_dir(path, module_name):
    """ Yield modules inside `path` parent directory """
    yield from modules_from_path(Path(path).parent, module_name)


def modules_from_path(path, module_name=None):
    """ Traverse current directory and yield python files imported as module """
    if path.is_file():
        yield import_module('.' + path.stem, module_name)
    elif path.is_dir():
        for file in path.iterdir():
            if '__pycache__' in str(file):
                continue
            if file.suffix == '.py' and file.stem != '__init__':
                yield from modules_from_path(file, module_name)
