"""Auto detect robot file type (it can be resource, general or init)"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from robocop.version_handling import LANG_SUPPORTED

if TYPE_CHECKING:
    from pathlib import Path

    from robot.parsing.model import File


def get_resource_with_lang(get_resource_method: Callable, source: Path, lang: str | None) -> File:
    if LANG_SUPPORTED:
        return get_resource_method(source, lang=lang)
    return get_resource_method(source)
