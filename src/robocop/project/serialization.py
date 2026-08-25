"""
Serialization of the data collected from a single source file.

The data is stored in the cache between the runs, so that the project context does not have to parse every file
again when nothing changed. Only plain types are used, so that the result can be stored with ``msgpack``.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from robocop.project.collector import CollectedFile, RawImport
from robocop.project.definitions import (
    ArgumentsSpec,
    ImportType,
    KeywordDefinition,
    KeywordUsage,
    Location,
    VariableDefinition,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

SERIALIZATION_VERSION = 2
"""Version of the format used to store the collected data. Bump it whenever the format changes."""


def _location_to_dict(location: Location) -> dict[str, Any]:
    return {
        "lineno": location.lineno,
        "col": location.col,
        "end_lineno": location.end_lineno,
        "end_col": location.end_col,
    }


def _location_from_dict(data: dict[str, Any], source: Path) -> Location:
    return Location(
        source=source,
        lineno=data["lineno"],
        col=data["col"],
        end_lineno=data["end_lineno"],
        end_col=data["end_col"],
    )


def _arguments_to_dict(arguments: ArgumentsSpec) -> dict[str, Any]:
    return {
        "positional": list(arguments.positional),
        "defaults": sorted(arguments.defaults),
        "var_positional": arguments.var_positional,
        "var_named": arguments.var_named,
        "named_only": list(arguments.named_only),
    }


def _arguments_from_dict(data: dict[str, Any]) -> ArgumentsSpec:
    return ArgumentsSpec(
        positional=tuple(data["positional"]),
        defaults=frozenset(data["defaults"]),
        var_positional=data["var_positional"],
        var_named=data["var_named"],
        named_only=tuple(data["named_only"]),
    )


def _keyword_to_dict(keyword: KeywordDefinition) -> dict[str, Any]:
    return {
        "name": keyword.name,
        "normalized_name": keyword.normalized_name,
        "location": _location_to_dict(keyword.location),
        "arguments": _arguments_to_dict(keyword.arguments),
        "embedded": {"pattern": keyword.embedded.pattern, "flags": keyword.embedded.flags}
        if keyword.embedded is not None
        else None,
        "is_private": keyword.is_private,
        "library_name": keyword.library_name,
    }


def _keyword_from_dict(data: dict[str, Any], source: Path) -> KeywordDefinition:
    embedded = data["embedded"]
    return KeywordDefinition(
        name=data["name"],
        normalized_name=data["normalized_name"],
        location=_location_from_dict(data["location"], source),
        arguments=_arguments_from_dict(data["arguments"]),
        embedded=re.compile(embedded["pattern"], embedded["flags"]) if embedded is not None else None,
        is_private=data["is_private"],
        library_name=data["library_name"],
    )


def _usage_to_dict(usage: KeywordUsage) -> dict[str, Any]:
    return {
        "name": usage.name,
        "normalized_name": usage.normalized_name,
        "location": _location_to_dict(usage.location),
        "arguments": list(usage.arguments),
        "argument_positions": [list(position) for position in usage.argument_positions],
        "name_contains_variable": usage.name_contains_variable,
        "bdd_prefix": usage.bdd_prefix,
        "is_template": usage.is_template,
    }


def _usage_from_dict(data: dict[str, Any], source: Path) -> KeywordUsage:
    return KeywordUsage(
        name=data["name"],
        normalized_name=data["normalized_name"],
        location=_location_from_dict(data["location"], source),
        arguments=tuple(data["arguments"]),
        argument_positions=tuple(tuple(position) for position in data["argument_positions"]),
        name_contains_variable=data["name_contains_variable"],
        bdd_prefix=data["bdd_prefix"],
        is_template=data["is_template"],
    )


def _variable_to_dict(variable: VariableDefinition) -> dict[str, Any]:
    return {
        "name": variable.name,
        "normalized_name": variable.normalized_name,
        "value": variable.value,
        "location": _location_to_dict(variable.location) if variable.location is not None else None,
    }


def _variable_from_dict(data: dict[str, Any], source: Path) -> VariableDefinition:
    location = data["location"]
    return VariableDefinition(
        name=data["name"],
        normalized_name=data["normalized_name"],
        value=data["value"],
        location=_location_from_dict(location, source) if location is not None else None,
    )


def _import_to_dict(raw_import: RawImport) -> dict[str, Any]:
    return {
        "import_type": raw_import.import_type.value,
        "name": raw_import.name,
        "location": _location_to_dict(raw_import.location),
        "args": list(raw_import.args),
        "alias": raw_import.alias,
    }


def _import_from_dict(data: dict[str, Any], source: Path) -> RawImport:
    return RawImport(
        import_type=ImportType(data["import_type"]),
        name=data["name"],
        location=_location_from_dict(data["location"], source),
        args=tuple(data["args"]),
        alias=data["alias"],
    )


def collected_file_to_dict(collected: CollectedFile) -> dict[str, Any]:
    """
    Convert data collected from a single file into plain types.

    The path of the file is not stored, since it is already the key of the cache entry. Locations are stored
    without the source path for the same reason.

    Returns:
        Dictionary that can be stored in the cache.

    """
    return {
        "version": SERIALIZATION_VERSION,
        "is_suite": collected.is_suite,
        "is_init_file": collected.is_init_file,
        "keywords": [_keyword_to_dict(keyword) for keyword in collected.keywords],
        "usages": [_usage_to_dict(usage) for usage in collected.usages],
        "variables": [_variable_to_dict(variable) for variable in collected.variables],
        "used_variables": sorted(collected.used_variables),
        "imports": [_import_to_dict(raw_import) for raw_import in collected.imports],
    }


def _restore_all(
    data: dict[str, Any], key: str, restore: Callable[[dict[str, Any], Path], Any], source: Path
) -> list[Any]:
    return [restore(item, source) for item in data[key]]


def collected_file_from_dict(data: dict[str, Any], path: Path) -> CollectedFile | None:
    """
    Restore data collected from a single file.

    Returns:
        CollectedFile, or None if the stored data was saved in a different format and cannot be restored.

    """
    if data.get("version") != SERIALIZATION_VERSION:
        return None
    try:
        return CollectedFile(
            path=path,
            is_suite=data["is_suite"],
            is_init_file=data["is_init_file"],
            keywords=_restore_all(data, "keywords", _keyword_from_dict, path),
            usages=_restore_all(data, "usages", _usage_from_dict, path),
            variables=_restore_all(data, "variables", _variable_from_dict, path),
            used_variables=set(data["used_variables"]),
            imports=_restore_all(data, "imports", _import_from_dict, path),
        )
    except (KeyError, TypeError, ValueError, re.error):  # pragma: no cover - defensive, corrupted cache
        return None
