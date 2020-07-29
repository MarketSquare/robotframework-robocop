""" Auto detect robot file type (it can be resource, general or init) """
import ast
import os
from enum import Enum
from pathlib import Path
from robot.api import get_model, get_resource_model, get_init_model
from robot.utils.robotpath import find_file
from robot.errors import DataError


class FileType(Enum):
    """
    Enum holding type of Robot file.
    """
    RESOURCE = 'resource'
    GENERAL = 'general'
    INIT = 'init'

    def get_parser(self):
        """ return parser (method) for given model type """
        return {
            'resource': get_resource_model,
            'general': get_model,
            'init': get_init_model
        }[self.value]


class FileTypeChecker(ast.NodeVisitor):
    """
    Check if file contains import statements. If the import is in list of files to be scanned, update its type
    from GENERAL to RESOURCE.
    """
    def __init__(self, files, exec_dir):
        self.files = files
        self.exec_dir = exec_dir
        self.source = None

    def visit_ResourceImport(self, node):  # noqa
        """
        Check all imports in scanned file. If one of our scanned file is imported somewhere else
        it means this file is resource type
         """
        path_normalized = normalize_robot_path(node.name, Path(self.source).parent, self.exec_dir)
        try:
            path_normalized = find_file(path_normalized, self.source.parent, file_type='Resource')
        except DataError:
            pass
        else:
            path = Path(path_normalized)
            if path in self.files:
                self.files[path] = FileType.RESOURCE


def normalize_robot_path(robot_path, curr_path, exec_path):
    normalized_path = str(robot_path).replace('${/}', os.path.sep)
    normalized_path = normalized_path.replace('${CURDIR}', str(curr_path))
    normalized_path = normalized_path.replace('${EXECDIR}', str(exec_path))
    return normalized_path
