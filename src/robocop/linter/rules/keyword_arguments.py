"""Checker for rules triggered by keyword arguments."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter.rules import VisitorChecker, arguments, keywords, spacing

if TYPE_CHECKING:
    from robot.parsing.model.blocks import Keyword
    from robot.parsing.model.statements import Arguments


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
