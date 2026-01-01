from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from robot.api import get_init_model, get_model, get_resource_model

try:
    from robot.api import Languages  # RF 6.0
except ImportError:
    Languages = None

from robocop.version_handling import LANG_SUPPORTED

if TYPE_CHECKING:
    from pathlib import Path

    from robot.parsing.model import File

    from robocop.config import Config


def _get_model_with_optional_lang(get_model_func: Callable, source: Path, lang: Languages) -> File:
    """
    Get Robot file tokenised model with optional language option.

    Language option was added in more recent Robot version and we need this code for backward compatibility.
    """
    if LANG_SUPPORTED:
        return get_model_func(source, lang=lang)
    return get_model_func(source)


def get_model_with_lang(source: Path, lang: Languages | None) -> File:
    if "__init__" in source.name:
        return _get_model_with_optional_lang(get_init_model, source, lang)
    if source.suffix == ".resource":
        return _get_model_with_optional_lang(get_resource_model, source, lang)
    return _get_model_with_optional_lang(get_model, source, lang)


@dataclass
class SourceFile:
    """
    Represents a source file with associated configuration, model, and content.

    Attributes:
        path: The path to the source file on the filesystem.
        config: The configuration settings associated with the source file.
        model: An optional model associated with the source file.
        source_lines: An optional list of lines representing the content of the source file.

    """

    path: Path
    config: Config
    _model: File | None = None
    source_lines: list[str] | None = None

    @property
    def model(self) -> File:
        if self._model is None:
            self._model = get_model_with_lang(self.path, self.config.languages)
        return self._model
