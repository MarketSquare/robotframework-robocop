from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from robot.api import get_init_model, get_model, get_resource_model
from robot.api.parsing import ModelVisitor

try:
    from robot.api import Languages  # RF 6.0
except ImportError:
    Languages = None

from robocop.embedded import extract_robot_blocks, reconstruct_source, shift_model_lines
from robocop.files import path_relative_to_cwd, resolve_path
from robocop.version_handling import LANG_SUPPORTED

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from robot.parsing.model import File
    from robot.parsing.model.statements import Statement

    from robocop.config.schema import Config
    from robocop.embedded import RobotCodeBlock
    from robocop.linter.diagnostics import Range
    from robocop.linter.fix import TextEdit


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
    _resolved_path: Path | None = None

    @property
    def resolved_path(self) -> Path:
        """Resolved path of the file, computed once per source file."""
        if self._resolved_path is None:
            self._resolved_path = resolve_path(self.path)
        return self._resolved_path

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
            loader: Callable[..., File] = get_init_model
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

    # Hooks used to support files with embedded Robot Framework code (Markdown, Python). For regular Robot files
    # they are no-ops, so the linter and formatter can treat every source file uniformly.

    @property
    def is_embedded(self) -> bool:
        """Whether the source file holds Robot code embedded in another format (Markdown, Python)."""
        return False

    @property
    def models(self) -> list[File]:
        """Models visited by AST checkers. Regular files expose a single model."""
        return [self.model]

    @property
    def fix_source_lines(self) -> list[str]:
        """Lines used when generating fixes. They share the coordinate space of :attr:`model`."""
        return self.source_lines

    @property
    def check_lines(self) -> list[tuple[int, str]]:
        """Physical lines (1-indexed) that raw-file rules should inspect."""
        return list(enumerate(self.source_lines, start=1))

    def offset_range(self, diag_range: Range) -> None:  # noqa: ARG002
        """Translate a diagnostic range from model coordinates to physical file coordinates (in place)."""
        return

    def prepare_fix_edits(self, edits: list[TextEdit]) -> list[TextEdit]:
        """Translate fix edits from model coordinates to physical file coordinates."""
        return edits


class EmbeddedSourceFile(SourceFile):
    """
    Source file holding Robot Framework code embedded in Markdown or Python files.

    The physical file (``source_lines``) keeps prose, fences and the original indentation untouched, so writing it
    back is a verbatim round-trip.

    Every code block is parsed into its own model whose line numbers are shifted to match the physical file, so AST
    checkers see each block independently (via :attr:`models`) and no false positives are produced by the prose
    between blocks. A combined model (:attr:`model`), where non-code lines are blanked out and code lines are
    dedented, is kept for consumers that need a single model spanning the whole file (disablers, documentation
    lines, templated-suite detection).

    Column positions differ between the model space and the physical file by the block indentation, so diagnostics
    and fixes generated against a model are translated back to physical coordinates before they are displayed or
    applied.
    """

    _blocks: list[RobotCodeBlock] | None = None
    _model_lines: list[str] | None = None
    _models: list[File] | None = None

    @property
    def is_embedded(self) -> bool:
        return True

    def _load_model(self, path_or_text: Path | str) -> File:
        text = self._physical_text(path_or_text)
        lines = text.splitlines(keepends=True)
        self._blocks = extract_robot_blocks(lines)
        reconstructed = reconstruct_source(lines, self._blocks)
        self._model_lines = reconstructed.splitlines(keepends=True)
        self._models = [
            self._build_block_model(block, self._model_lines) for block in self._blocks if not block.is_empty
        ]
        return self._build_model(reconstructed)

    def _build_model(self, source: str) -> File:
        from robot.api import get_model as _get_model  # noqa: PLC0415

        if LANG_SUPPORTED:
            model = _get_model(source, lang=self.config.languages)
        else:
            model = _get_model(source)
        model.source = self.path
        return model

    def _build_block_model(self, block: RobotCodeBlock, model_lines: list[str]) -> File:
        source = "".join(model_lines[block.start_line - 1 : block.end_line])
        model = self._build_model(source)
        return shift_model_lines(model, block.start_line - 1)

    def format_blocks(self) -> list[tuple[RobotCodeBlock, File]]:
        """
        Return every non-empty block paired with a freshly parsed model for formatting.

        The models use block-local line numbers (starting at 1), which is what the formatters and the model writer
        expect. Re-indentation and splicing back into the physical file is handled by the caller.
        """
        blocks = []
        for block in self.blocks:
            if block.is_empty:
                continue
            source = "".join(self.model_lines[block.start_line - 1 : block.end_line])
            blocks.append((block, self._build_model(source)))
        return blocks

    def _physical_text(self, path_or_text: Path | str) -> str:
        if isinstance(path_or_text, str):
            return path_or_text
        with open(path_or_text, encoding="utf-8", newline="") as f:
            return f.read()

    @property
    def blocks(self) -> list[RobotCodeBlock]:
        if self._blocks is None:
            _ = self.model  # triggers extraction
        return self._blocks or []

    @property
    def models(self) -> list[File]:
        if self._models is None:
            _ = self.model
        return self._models or []

    @property
    def model_lines(self) -> list[str]:
        if self._model_lines is None:
            _ = self.model
        return self._model_lines or []

    @property
    def fix_source_lines(self) -> list[str]:
        return self.model_lines

    @property
    def check_lines(self) -> list[tuple[int, str]]:
        """Only the (dedented) lines that belong to a Robot code block are inspected by raw-file rules."""
        lines = self.model_lines
        return [
            (lineno, lines[lineno - 1])
            for block in self.blocks
            for lineno in range(block.start_line, block.end_line + 1)
            if 0 < lineno <= len(lines)
        ]

    def base_indent(self, lineno: int) -> int:
        """Return the block indentation (number of columns) for the given physical line, or 0 outside any block."""
        for block in self.blocks:
            if block.contains(lineno):
                return len(block.indent)
        return 0

    def offset_range(self, diag_range: Range) -> None:
        start_indent = self.base_indent(diag_range.start.line)
        end_indent = self.base_indent(diag_range.end.line)
        diag_range.start.character += start_indent
        diag_range.end.character += end_indent

    def prepare_fix_edits(self, edits: list[TextEdit]) -> list[TextEdit]:
        from robocop.linter.fix import TextEditKind  # noqa: PLC0415

        for edit in edits:
            indent = self.base_indent(edit.start_line)
            if not indent:
                continue
            if edit.kind == TextEditKind.REPLACEMENT:
                edit.start_col += indent
                edit.end_col += indent
            elif edit.kind in (TextEditKind.REPLACEMENT_LINES, TextEditKind.INSERTION):
                edit.replacement = self._reindent(edit.replacement, indent)
        return edits

    @staticmethod
    def _reindent(text: str, indent: int) -> str:
        prefix = " " * indent
        return "".join(f"{prefix}{line}" if line.strip() else line for line in text.splitlines(keepends=True))


def build_source_file(path: Path, config: Config) -> SourceFile:
    """Create the right :class:`SourceFile` for the given path, based on its extension."""
    from robocop.embedded import is_embedded_extension  # noqa: PLC0415

    if is_embedded_extension(path.suffix):
        return EmbeddedSourceFile(path=path, config=config)
    return SourceFile(path=path, config=config)


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
