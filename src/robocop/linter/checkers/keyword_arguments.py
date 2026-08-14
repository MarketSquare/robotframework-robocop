"""Checker for rules triggered by keyword arguments."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter.rules import ProjectChecker, VisitorChecker, arguments, keywords, spacing
from robocop.source_file import SourceFile

if TYPE_CHECKING:
    from robot.parsing.model.blocks import Keyword
    from robot.parsing.model.statements import Arguments

    from robocop.config.manager import ConfigManager
    from robocop.linter.diagnostics import Diagnostic
    from robocop.project.context import ProjectContext
    from robocop.project.definitions import ArgumentsMismatch, KeywordUsage
    from robocop.source_file import VirtualSourceFile


class ArgumentsChecker(VisitorChecker):
    """Checker for rules reported for the keyword arguments."""

    first_argument_in_new_line: spacing.FirstArgumentInNewLineRule
    arguments_per_line: arguments.ArgumentsPerLineRule
    undefined_argument_default: arguments.UndefinedArgumentDefaultRule
    duplicated_argument_name: arguments.DuplicatedArgumentRule
    no_embedded_keyword_arguments: keywords.NoEmbeddedKeywordArgumentsRule

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
        self.no_embedded_keyword_arguments.check(node)
        self.generic_visit(node)

    def visit_Arguments(self, node: Arguments) -> None:  # noqa: N802
        self.first_argument_in_new_line.check(node)
        self.arguments_per_line.check(node)
        self.undefined_argument_default.check(node)
        self.duplicated_argument_name.check(node)


class ProjectArgumentsChecker(ProjectChecker):
    """Checker for keyword arguments validated against definitions from the whole project."""

    invalid_argument_count: arguments.InvalidArgumentCountRule

    def scan_project(
        self,
        project_source_file: SourceFile | VirtualSourceFile,
        config_manager: ConfigManager,  # noqa: ARG002
        context: ProjectContext | None = None,
    ) -> list[Diagnostic]:
        self.issues = []
        if context is None:
            return self.issues
        for project_file, usage in context.iter_usages():
            mismatch = self._validate_usage(context, usage)
            if mismatch is None:
                continue
            self.report(
                self.invalid_argument_count,
                source=SourceFile(path=project_file.path, config=project_source_file.config),
                keyword_name=usage.name,
                expected=mismatch.expected,
                provided=mismatch.provided,
                missing=self._describe_missing(mismatch),
                lineno=usage.location.lineno,
                col=usage.location.col,
                end_lineno=usage.location.end_lineno,
                end_col=usage.location.end_col,
            )
        return self.issues

    @staticmethod
    def _describe_missing(mismatch: ArgumentsMismatch) -> str:
        if not mismatch.missing:
            return ""
        missing = ", ".join(f"${{{name}}}" for name in mismatch.missing)
        return f", missing {missing}"

    @staticmethod
    def _validate_usage(context: ProjectContext, usage: KeywordUsage) -> ArgumentsMismatch | None:
        if usage.is_template or usage.name_contains_variable or usage.has_argument_expansion:
            return None
        definitions = context.resolve_keyword(usage)
        if len(definitions) != 1:
            return None  # not defined in the project, or ambiguous
        definition = definitions[0]
        if definition.has_embedded_arguments:
            return None
        return definition.arguments.validate_call(usage.arguments)
