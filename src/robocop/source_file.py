from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from robot.api import get_init_model, get_model, get_resource_model
from robot.api.parsing import ModelVisitor

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
        updated: Whether or not the source file has been updated.
        _model: An optional model associated with the source file.
        _source_lines: An optional list of lines representing the content of the source file.

    """

    path: Path
    config: Config
    updated: bool = False
    _model: File | None = None
    _source_lines: list[str] | None = None

    @property
    def model(self) -> File:
        if self._model is None:
            self._model = self._load_model()
        return self._model

    @property
    def source_lines(self) -> list[str]:
        """
        Retrieves the source code lines for the associated path or model.

        Lazily loads and caches the source lines by reading from the file path
        with UTF-8 encoding. If the file cannot be read due to an OSError, it
        falls back to collecting statement lines from the model as a text
        representation.

        Returns:
            list[str]: A list of source code lines.

        """
        if self._source_lines is None:
            try:
                self._source_lines = self.path.read_text(encoding="utf-8").splitlines(keepends=True)
            except OSError:
                self._source_lines = StatementLinesCollector(self.model).text.splitlines()  # TODO: no ends
        return self._source_lines

    def _load_model(self) -> File:
        """Determine the correct model loader based on the file type and loads it."""
        if "__init__" in self.path.name:
            loader: Callable = get_init_model
        elif self.path.suffix == ".resource":
            loader: Callable = get_resource_model
        else:
            loader: Callable = get_model

        if LANG_SUPPORTED:
            return loader(self.path, lang=self.config.languages)
        return loader(self.path)


class VirtualSourceFile(SourceFile):
    @property
    def source_lines(self) -> list[str]:
        return []


class StatementLinesCollector(ModelVisitor):
    """Used to get a writeable presentation of a Robot Framework model."""

    def __init__(self, model):
        self.text = ""
        self.visit(model)

    def visit_Statement(self, node):  # noqa: N802
        for token in node.tokens:
            self.text += token.value

    def __eq__(self, other):
        return other.text == self.text

    def __hash__(self):
        return hash(self.text)
