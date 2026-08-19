"""Checker for rules triggered by keyword arguments."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter.rules import ProjectChecker, VisitorChecker, arguments, keywords, spacing
from robocop.parsing.run_keywords import is_run_keyword
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
        context: ProjectContext,
    ) -> list[Diagnostic]:
        self.issues = []
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
        # TODO: each resource imports BuiltIn, and then resolve_keyword returns BuiltIn from each resource, so != 1
        definitions = context.resolve_keyword(usage)
        if len(definitions) != 1:
            return None  # not defined in the project, or ambiguous
        definition = definitions[0]
        if definition.has_embedded_arguments:
            return None
        return definition.arguments.validate_call(usage.arguments)


class ProjectArgumentNamesChecker(ProjectChecker):
    """Checker for rules that require argument names from the keyword definitions in the whole project."""

    missing_argument_name: arguments.MissingArgumentNameRule

    def scan_project(
        self,
        project_source_file: SourceFile | VirtualSourceFile,
        config_manager: ConfigManager,  # noqa: ARG002
        context: ProjectContext,
    ) -> list[Diagnostic]:
        self.issues = []
        for project_file, usage in context.iter_usages():
            named_arguments = self._find_positional_arguments(context, usage)
            if len(named_arguments) < self.missing_argument_name.min_arguments:
                continue
            source = SourceFile(path=project_file.path, config=project_source_file.config)
            for index, argument_name in named_arguments:
                lineno, col, end_col = usage.argument_positions[index]
                self.report(
                    self.missing_argument_name,
                    source=source,
                    keyword_name=usage.name,
                    argument_name=argument_name,
                    lineno=lineno,
                    col=col,
                    end_lineno=lineno,
                    end_col=end_col,
                )
        return self.issues

    def _find_positional_arguments(self, context: ProjectContext, usage: KeywordUsage) -> list[tuple[int, str]]:
        """
        Find arguments passed by the position together with their names from the keyword definition.

        Returns:
            List of ``(index in the call, argument name)`` pairs, empty if the call should not be reported.

        """
        if usage.is_template or usage.name_contains_variable or usage.has_argument_expansion:
            return []
        if len(usage.arguments) != len(usage.argument_positions):
            return []  # positions are missing, for example when data comes from an older cache
        if is_run_keyword(usage.name):
            return []  # arguments of the run keywords are keyword names and their arguments
        definitions = context.resolve_keyword(usage)
        if len(definitions) != 1:
            return []  # not defined in the project, or ambiguous
        definition = definitions[0]
        if definition.has_embedded_arguments or (
            definition.is_from_library and self.missing_argument_name.ignore_library_keywords
        ):
            return []
        return definition.arguments.name_positional_arguments(usage.arguments) or []
