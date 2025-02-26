"""Auto detect robot file type (it can be resource, general or init)"""

from __future__ import annotations

import ast
import os
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from robot.api import get_init_model, get_model, get_resource_model
from robot.errors import DataError
from robot.utils.robotpath import find_file

import robocop.linter.exceptions
from robocop.linter.utils.misc import rf_supports_lang

if TYPE_CHECKING:
    from robot.parsing.model import File
    from robot.parsing.model.statements import ResourceImport


@robocop.linter.exceptions.handle_robot_errors
def get_resource_with_lang(get_resource_method: Callable, source: Path, lang: str | None) -> File:
    if rf_supports_lang():
        return get_resource_method(source, lang=lang)
    return get_resource_method(source)


class FileType(Enum):
    """Enum holding type of Robot file."""

    RESOURCE = "resource"
    GENERAL = "general"
    INIT = "init"

    def get_parser(self) -> Callable:
        """Return parser (method) for given model type"""
        return {
            "resource": get_resource_model,
            "general": get_model,
            "init": get_init_model,
        }[self.value]


class FileTypeChecker(ast.NodeVisitor):
    """
    Check if file contains import statements.

    If the import is in list of files to be scanned, update its type
    from GENERAL to RESOURCE.
    """

    def __init__(self, exec_dir: Path):
        self.resource_files = set()
        self.exec_dir = exec_dir
        self.source = None

    def visit_ResourceImport(self, node: ResourceImport) -> None:  # noqa: N802
        """
        Check all imports in scanned file.

        If one of our scanned file is imported somewhere else
        it means this file is resource type
        """
        path_normalized = normalize_robot_path(node.name, Path(self.source).parent, self.exec_dir)
        try:
            path_normalized = find_file(path_normalized, self.source.parent, file_type="Resource")
        except DataError:
            pass
        else:
            path = Path(path_normalized)
            self.resource_files.add(path)


def normalize_robot_path(robot_path: str, curr_path: Path, exec_path: Path) -> str:
    normalized_path = str(robot_path).replace("${/}", os.path.sep)
    normalized_path = normalized_path.replace("${CURDIR}", str(curr_path))
    return normalized_path.replace("${EXECDIR}", str(exec_path))
