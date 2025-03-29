"""Auto detect robot file type (it can be resource, general or init)"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from robocop import errors
from robocop.linter.utils.misc import rf_supports_lang

if TYPE_CHECKING:
    from pathlib import Path

    from robot.parsing.model import File


@errors.handle_robot_errors
def get_resource_with_lang(get_resource_method: Callable, source: Path, lang: str | None) -> File:
    if rf_supports_lang():
        return get_resource_method(source, lang=lang)
    return get_resource_method(source)
