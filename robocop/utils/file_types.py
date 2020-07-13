import ast
import os
from enum import Enum
from pathlib import Path
from robot.api import get_model, get_resource_model, get_init_model
from robot.utils.robotpath import find_file
from robot.errors import DataError


class FileType(Enum):
    RESOURCE = 'resource'
    GENERAL = 'general'
    INIT = 'init'

    def get_parser(self):
        return {
            'resource': get_resource_model,
            'general': get_model,
            'init': get_init_model
        }[self.value]


class FileTypeChecker(ast.NodeVisitor):
    def __init__(self, files):
        self.files = files
        self.source = None

    def visit_ResourceImport(self, node):
        path_normalized = node.name.replace('${/}', os.path.sep)
        try:
            path_normalized = find_file(path_normalized, self.source.parent, file_type='Resource')
        except DataError:
            pass
        else:
            path = Path(path_normalized)
            if path in self.files:
                self.files[path] = FileType.RESOURCE

