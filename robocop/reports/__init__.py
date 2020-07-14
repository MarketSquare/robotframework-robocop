from pathlib import Path
from astroid import modutils


def init(linter):
    seen = set()
    for file in Path(__file__).parent.iterdir():
        if file.stem in seen or '__pycache__' in str(file):
            continue
        try:
            if file.is_dir() or (file.suffix in ('.py') and file.stem != '__init__'):
                module = modutils.load_module_from_file(str(file))
                module.register(linter)
                seen.add(file.stem)
        except IOError as error:
            print(error)
