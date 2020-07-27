"""
Reports are configurable summaries after lint scan. For example it could be total number of issues discovered.
They are dynamically loaded during setup according to command line configuration.
"""
from robocop.utils import modules_in_current_dir


def init(linter):
    for module in modules_in_current_dir(__file__, __name__):
        try:
            module.register(linter)
        except IOError as error:
            print(error)
