"""
Project level context for Robocop rules.

This package provides data collected from the whole project, instead of a single file. It is used by
``ProjectChecker`` based rules which need to know about other files, for example to detect unused keywords or
keyword calls with an invalid number of arguments.

The main entry point is :class:`ProjectContext`, built by :func:`build_project_context` and passed to
``ProjectChecker.scan_project``.
"""

from robocop.project.collector import CollectedFile, ProjectFileCollector, RawImport
from robocop.project.context import KeywordIndex, ProjectContext, ProjectFile, build_project_context
from robocop.project.definitions import (
    ArgumentsSpec,
    ImportStatus,
    ImportType,
    KeywordDefinition,
    KeywordUsage,
    Location,
    ResolvedImport,
    VariableDefinition,
    parse_embedded_arguments,
)
from robocop.project.imports import ImportResolver
from robocop.project.variables import VariableScope

__all__ = [
    "ArgumentsSpec",
    "CollectedFile",
    "ImportResolver",
    "ImportStatus",
    "ImportType",
    "KeywordDefinition",
    "KeywordIndex",
    "KeywordUsage",
    "Location",
    "ProjectContext",
    "ProjectFile",
    "ProjectFileCollector",
    "RawImport",
    "ResolvedImport",
    "VariableDefinition",
    "VariableScope",
    "build_project_context",
    "parse_embedded_arguments",
]
