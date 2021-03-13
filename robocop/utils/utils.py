from pathlib import Path
from importlib import import_module
import importlib.util

from robocop.exceptions import InvalidExternalCheckerError

from robot.api import Token
from robot.version import VERSION


IS_RF4 = VERSION.startswith('4')
DISABLED_IN_4 = frozenset(('nested-for-loop', 'invalid-comment'))
ENABLED_IN_4 = frozenset(('if-can-be-used', 'else-not-upper-case'))


def modules_in_current_dir(path, module_name):
    """ Yield modules inside `path` parent directory """
    yield from modules_from_path(Path(path).parent, module_name)


def modules_from_paths(paths):
    for path in paths:
        path = Path(path)
        if not path.exists():
            raise InvalidExternalCheckerError(path)
        if path.is_dir():
            yield from modules_from_paths([file for file in path.iterdir() if '__pycache__' not in str(file)])
        else:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            mod = importlib.util.module_from_spec(spec)

            spec.loader.exec_module(mod)
            yield mod


def modules_from_path(path, module_name=None, relative='.'):
    """ Traverse current directory and yield python files imported as module """
    if path.is_file():
        yield import_module(relative + path.stem, module_name)
    elif path.is_dir():
        for file in path.iterdir():
            if '__pycache__' in str(file):
                continue
            if file.suffix == '.py' and file.stem != '__init__':
                yield from modules_from_path(file, module_name, relative)


def normalize_robot_name(name):
    return name.replace(' ', '').replace('_', '').lower()


def keyword_col(node):
    keyword_token = node.get_token(Token.KEYWORD)
    if keyword_token is None:
        return 0
    return keyword_token.col_offset
