from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from robot.api import get_init_model, get_model, get_resource_model
from robot.api.parsing import ModelVisitor

try:
    from robot.api import Languages  # RF 6.0
except ImportError:
    Languages = None

from robocop.files import path_relative_to_cwd
from robocop.version_handling import LANG_SUPPORTED

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from robot.parsing.model import File
    from robot.parsing.model.statements import Statement

    from robocop.config import Config


@dataclass
class SourceFile:
    """
    Represents a source file with associated configuration, model, and content.

    Attributes:
        path: The path to the source file on the filesystem.
        config: The configuration settings associated with the source file.
        modified: Whether or not the source file has been updated.
        _model: An optional model associated with the source file.
        _source_lines: An optional list of lines representing the content of the source file.
        _original_source_lines: An optional copy of the original source lines for diff comparison.

    """

    path: Path
    config: Config
    modified: bool = False
    _model: File | None = None
    _source_lines: list[str] | None = None
    _original_source_lines: list[str] | None = None

    @property
    def relative_path(self) -> Path:
        return path_relative_to_cwd(self.path)

    @property
    def model(self) -> File:
        if self._model is None:
            self._model = self._load_model(self.path)
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
        # TODO: potential issue: robotcode send model with the updated code, but the file is not saved to disk yet
        if self._source_lines is None:
            try:
                self._source_lines = self._read_lines()
            except OSError:
                self._source_lines = StatementLinesCollector(self.model).text.splitlines()
            # Save original content for diff comparison
            if self._original_source_lines is None and self.config.linter.diff:
                self._original_source_lines = self._source_lines.copy()
        return self._source_lines

    @property
    def original_source_lines(self) -> list[str]:
        """
        Get the original source lines before any modifications.

        Returns:
            list[str]: A list of original source code lines.

        """
        if self._original_source_lines is None:
            # Trigger loading of source_lines which will also set the original lines
            _ = self.source_lines
        if self._original_source_lines is None:  # failed to load
            return []
        return self._original_source_lines

    def _read_lines(self) -> list[str]:
        """
        Read the physical file lines while keeping the original EOL.

        Returns:
            list[str]: A list of source code lines.

        """
        with open(self.path, encoding="utf-8", newline="") as f:
            return f.readlines()

    def _load_model(self, path_or_text: Path | str) -> File:
        """Determine the correct model loader based on the file type and loads it."""
        if "__init__" in self.path.name:
            loader: Callable = get_init_model
        elif self.path.suffix == ".resource":
            loader = get_resource_model
        else:
            loader = get_model

        if LANG_SUPPORTED:
            return loader(path_or_text, lang=self.config.languages)
        return loader(path_or_text)

    def reload_model(self) -> None:
        """
        Reload the model from modified source lines.

        This method should be called after applying fixes to update the internal
        model representation. It only reloads if the file has been modified in memory.
        The model is reconstructed from the current source_lines content.

        """
        source_content = "".join(self.source_lines)
        self._model = self._load_model(source_content)

    def write_changes(self) -> None:
        """
        Write the modified source lines back to the file.

        Writes the current source_lines content to the file path with UTF-8 encoding.
        This should be called after making changes to persist them to disk.

        """
        if not self.modified:
            return
        with open(self.path, "w", encoding="utf-8", newline="") as f:
            f.writelines(self.source_lines)


class VirtualSourceFile(SourceFile):
    @property
    def source_lines(self) -> list[str]:
        return []


class StatementLinesCollector(ModelVisitor):  # type: ignore[misc]
    """Used to get a writeable presentation of a Robot Framework model."""

    def __init__(self, model: File) -> None:
        self.tokens: list[str] = []
        self.visit(model)
        self.text = "".join(self.tokens)

    def visit_Statement(self, node: Statement) -> None:  # noqa: N802
        for token in node.tokens:
            self.tokens.append(token.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StatementLinesCollector):
            raise NotImplementedError
        return other.text == self.text

    def __hash__(self) -> int:
        return hash(self.text)
