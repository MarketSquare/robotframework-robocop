"""
Worker used to import Robot Framework libraries and read their keywords.

Importing a library executes user code, which can be slow, can fail in unexpected ways or can even never finish.
By default Robocop calls :func:`load_library` directly, but with the ``--library-workers`` option the import happens
in a separate process started with ``python -m robocop.project._libdoc_worker`` and communicating with Robocop over
JSON. The request is read from the standard input and the response is written to the file provided in the request,
so that anything the library prints during the import does not corrupt the response. The parent process can safely
kill this process on timeout.

The module does not import Robocop, so that it can be started even if the inspected library modifies ``sys.path``.
"""

from __future__ import annotations

import io
import json
import sys
import traceback
import warnings
from contextlib import contextmanager, redirect_stderr, redirect_stdout, suppress
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

ARGUMENT_SEPARATOR = "::"


@contextmanager
def _silenced_robot_logger() -> Iterator[None]:
    """Stop Robot Framework from printing library import errors and warnings to the console."""
    try:
        from robot.output import LOGGER  # noqa: PLC0415
    except ImportError:  # pragma: no cover - defensive, Robot Framework is a required dependency
        yield
        return
    # Messages are not cached either, since cached messages are printed when a new logger is registered.
    with suppress(AttributeError):
        LOGGER.disable_message_cache()
    with LOGGER.cache_only:
        yield


@contextmanager
def silenced() -> Iterator[None]:
    """Hide everything the imported library and Robot Framework print while the library is imported."""
    discarded = io.StringIO()
    # Robot Framework writes the output captured during the library import directly to the original streams.
    original_stdout, original_stderr = sys.__stdout__, sys.__stderr__
    sys.__stdout__ = discarded  # type: ignore[assignment, misc]
    sys.__stderr__ = discarded  # type: ignore[assignment, misc]
    try:
        with (
            warnings.catch_warnings(),
            redirect_stdout(discarded),
            redirect_stderr(discarded),
            _silenced_robot_logger(),
        ):
            warnings.simplefilter("ignore")
            yield
    finally:
        sys.__stdout__ = original_stdout  # type: ignore[misc]
        sys.__stderr__ = original_stderr  # type: ignore[misc]


def _argument_spec(spec: Any) -> dict[str, Any]:
    """
    Convert Robot Framework ``ArgumentSpec`` into a plain dictionary.

    Returns:
        Dictionary matching the fields of the ``ArgumentsSpec`` used by Robocop.

    """
    defaults = getattr(spec, "defaults", None) or {}
    positional_only = list(getattr(spec, "positional_only", None) or [])
    positional_or_named = list(getattr(spec, "positional_or_named", None) or [])
    return {
        "positional": [str(name) for name in (*positional_only, *positional_or_named)],
        "defaults": [str(name) for name in defaults],
        "var_positional": getattr(spec, "var_positional", None),
        "var_named": getattr(spec, "var_named", None),
        "named_only": [str(name) for name in (getattr(spec, "named_only", None) or [])],
    }


def _keywords(library: Any) -> list[dict[str, Any]]:
    """
    Read keywords from the imported library documentation.

    Returns:
        List of dictionaries describing every keyword of the library.

    """
    return [
        {
            "name": keyword.name,
            "arguments": _argument_spec(keyword.args),
            "source": str(keyword.source) if keyword.source else None,
            "lineno": keyword.lineno or 0,
        }
        for keyword in library.keywords
    ]


def load_library(request: dict[str, Any]) -> dict[str, Any]:
    """
    Import the library described by the request and read its keywords.

    Returns:
        Response with either the library keywords or the description of the failure.

    """
    for search_path in reversed(request.get("search_paths") or []):
        if search_path not in sys.path:
            sys.path.insert(0, search_path)
    name = request["name"]
    args = request.get("args") or []
    if args:
        name = ARGUMENT_SEPARATOR.join([name, *args])
    try:
        from robot.libdocpkg import LibraryDocumentation  # noqa: PLC0415

        with silenced():
            library = LibraryDocumentation(name)
            keywords = _keywords(library)
        return {
            "status": "ok",
            "name": library.name,
            "source": str(library.source) if library.source else None,
            "keywords": keywords,
        }
    except BaseException as error:  # noqa: BLE001 - importing a library executes arbitrary code
        message = f"{type(error).__name__}: {error}".strip()
        return {
            "status": "error",
            "error": message.splitlines()[0] if message else type(error).__name__,
            "traceback": traceback.format_exc(),
        }


def main() -> None:
    """Read the request from the standard input and write the response to the file requested by the parent."""
    request = json.loads(sys.stdin.read())
    response = load_library(request)
    with open(request["output"], "w", encoding="utf-8") as output:
        json.dump(response, output)


if __name__ == "__main__":
    main()
