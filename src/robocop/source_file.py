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
    _source_lines: list[str] | None = None

    @property
    def model(self) -> File:
        if self._model is None:
            self._model = self._load_model()
        return self._model

    def _load_model(self) -> File:
        """Determine the correct model loader based on file type and loads it."""
        if "__init__" in self.path.name:
            loader: Callable = get_init_model
        elif self.path.suffix == ".resource":
            loader: Callable = get_resource_model
        else:
            loader: Callable = get_model

        if LANG_SUPPORTED:
            return loader(self.path, lang=self.config.languages)
        return loader(self.path)
