"""Checker for complexity metrics of test cases and keywords."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter.rules import VisitorChecker, complexity
from robocop.linter.utils.complexity import compute_complexity

if TYPE_CHECKING:
    from robot.parsing.model import Keyword, TestCase


class ComplexityChecker(VisitorChecker):
    """Compute complexity of each test case and keyword once and pass it to the complexity rules."""

    cyclomatic_complexity_keyword: complexity.CyclomaticComplexityKeywordRule
    cyclomatic_complexity_test_case: complexity.CyclomaticComplexityTestCaseRule
    cognitive_complexity_keyword: complexity.CognitiveComplexityKeywordRule
    cognitive_complexity_test_case: complexity.CognitiveComplexityTestCaseRule

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
        if node.name.lstrip().startswith("#"):
            return
        if not (self.cyclomatic_complexity_keyword.enabled or self.cognitive_complexity_keyword.enabled):
            return
        result = compute_complexity(node)
        self.cyclomatic_complexity_keyword.check(node, result)
        self.cognitive_complexity_keyword.check(node, result)

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        if not (self.cyclomatic_complexity_test_case.enabled or self.cognitive_complexity_test_case.enabled):
            return
        result = compute_complexity(node)
        self.cyclomatic_complexity_test_case.check(node, result)
        self.cognitive_complexity_test_case.check(node, result)
