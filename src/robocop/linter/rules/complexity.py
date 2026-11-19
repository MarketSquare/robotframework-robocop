"""Complexity checkers"""

from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter import sonar_qube
from robocop.linter.rules import Rule, RuleParam, RuleSeverity, SeverityThreshold
from robocop.linter.utils.misc import last_lineno

if TYPE_CHECKING:
    from collections.abc import Callable

    from robot.parsing.model.blocks import Keyword, TestCase

    from robocop.linter.utils.complexity import ComplexityResult

COMPLEXITY_SONAR_QUBE_ATTRS = sonar_qube.SonarQubeAttributes(
    clean_code=sonar_qube.CleanCodeAttribute.FOCUSED,
    issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
)
CYCLOMATIC_FIX = "Split the logic into smaller keywords or replace branching with data."
COGNITIVE_FIX = "Reduce nesting with early exits or extract nested blocks into keywords."


def _report_if_too_complex(
    rule: Rule,
    node: Keyword | TestCase,
    complexity: int,
    allowed: int,
    contributors: Callable[[], str],
) -> None:
    """Report ``node`` when ``complexity`` exceeds ``allowed``, with the main contributors in the message."""
    if not rule.enabled or complexity <= allowed:
        return
    rule.report(
        block_name=node.name,
        complexity=complexity,
        allowed_complexity=allowed,
        contributors=contributors(),
        node=node,
        end_col=node.col_offset + len(node.name) + 1,
        extended_disablers=(node.lineno, last_lineno(node)),
        sev_threshold_value=complexity,
    )


class CyclomaticComplexityKeywordRule(Rule):
    """
    Keyword has too high cyclomatic complexity.

    Cyclomatic complexity (McCabe) is ``1 +`` the number of decision points: ``IF``, ``ELSE IF``, ``FOR``,
    ``WHILE``, each ``EXCEPT`` and each condition of a conditional BuiltIn keyword (``Run Keyword If``,
    ``Run Keyword Unless``, ``Set Variable If``, ``Skip If``, ``Pass Execution If``, ``Return From Keyword If``,
    ``Run Keyword And Return If``, ``Exit For Loop If``, ``Continue For Loop If``), also with a BDD prefix such as
    ``Given``. ``ELSE``, ``TRY``, ``FINALLY``, ``GROUP`` and boolean operators are not counted.

    It approximates the number of paths through the code. A wide keyword with many flat branches scores high:

        *** Keywords ***
        Select Browser Options    # cyclomatic complexity 4
            IF    $browser == 'chrome'
                Set Chrome Options
            ELSE IF    $browser == 'firefox'
                Set Firefox Options
            ELSE
                Set Default Options
            END
            FOR    ${option}    IN    @{extra_options}
                Add Option    ${option}
            END

    The message lists the decision points by kind, for example ``3 IF, 2 ELSE IF, 1 FOR``. Split such keywords
    into smaller ones, or replace branching with data (for example a dictionary lookup). See
    ``cognitive-complexity-keyword`` for a metric that also penalises nesting.

    Not analysed: keywords called from ``[Setup]`` / ``[Teardown]``, and run keywords nested inside conditional
    keywords (``Run Keyword If    $a    Run Keyword If    $b    ...``), where only the outer keyword counts.

    """

    name = "cyclomatic-complexity-keyword"
    rule_id = "CPX01"
    message = (
        "Keyword '{block_name}' has too high cyclomatic complexity ({complexity}/{allowed_complexity}), "
        "decision points: {contributors}"
    )
    severity = RuleSeverity.WARNING
    enabled = False
    parameters = [
        RuleParam(name="max_complexity", default=10, converter=int, desc="allowed cyclomatic complexity"),
    ]
    severity_threshold = SeverityThreshold(
        "max_complexity", compare_method="greater", substitute_value="allowed_complexity"
    )
    added_in_version = "9.5.0"
    sonar_qube_attrs = COMPLEXITY_SONAR_QUBE_ATTRS
    fix_suggestion = CYCLOMATIC_FIX

    def check(self, node: Keyword, result: ComplexityResult) -> None:
        _report_if_too_complex(self, node, result.cyclomatic, self.max_complexity, result.cyclomatic_contributors)


class CyclomaticComplexityTestCaseRule(Rule):
    """
    Test case or task has too high cyclomatic complexity.

    Same metric as ``cyclomatic-complexity-keyword``, for test cases and tasks. Tests are usually flatter than
    keywords, so the default limit is lower. Move branching into keywords so the test reads as a scenario.

    """

    name = "cyclomatic-complexity-test-case"
    rule_id = "CPX02"
    message = (
        "Test case '{block_name}' has too high cyclomatic complexity ({complexity}/{allowed_complexity}), "
        "decision points: {contributors}"
    )
    severity = RuleSeverity.WARNING
    enabled = False
    parameters = [
        RuleParam(name="max_complexity", default=7, converter=int, desc="allowed cyclomatic complexity"),
    ]
    severity_threshold = SeverityThreshold(
        "max_complexity", compare_method="greater", substitute_value="allowed_complexity"
    )
    added_in_version = "9.5.0"
    sonar_qube_attrs = COMPLEXITY_SONAR_QUBE_ATTRS
    fix_suggestion = CYCLOMATIC_FIX

    def check(self, node: TestCase, result: ComplexityResult) -> None:
        _report_if_too_complex(self, node, result.cyclomatic, self.max_complexity, result.cyclomatic_contributors)


class CognitiveComplexityKeywordRule(Rule):
    """
    Keyword has too high cognitive complexity.

    Cognitive complexity (SonarSource) measures how hard the code is to understand. Unlike cyclomatic complexity
    it penalises nesting:

    - ``IF`` (also inline), ``FOR``, ``WHILE``, ``EXCEPT`` and conditional BuiltIn keywords (``Run Keyword If``,
      ``Set Variable If``, ``Skip If``, ...) cost ``1 +`` the current nesting level,
    - ``ELSE IF``, ``ELSE`` and the ``ELSE`` branch of ``TRY`` cost ``1``,
    - every sequence of like boolean operators in a condition of ``IF``, ``ELSE IF``, ``WHILE`` or a conditional
      BuiltIn keyword costs ``1`` (``$a and $b`` is 1, ``$a and $b or $c`` is 2),
    - ``TRY``, ``FINALLY``, ``GROUP``, ``BREAK``, ``CONTINUE`` and ``RETURN`` cost nothing.

    Bodies of ``IF`` / ``ELSE IF`` / ``ELSE``, ``FOR``, ``WHILE``, ``EXCEPT`` and ``TRY ELSE`` are one nesting level
    deeper. Example:

        *** Keywords ***
        Process Items    # cognitive complexity 7
            FOR    ${item}    IN    @{items}                  # +1
                IF    $item.valid                             # +2 (nesting 1)
                    IF    $item.priority > 5 and $urgent      # +3 (nesting 2) +1 (and)
                        Handle Urgent    ${item}
                    END
                END
            END

    The message lists the three lines that add the most, for example
    ``line 5 +4 (IF at nesting 2, boolean operators)``. Flatten the code with early exits (``CONTINUE``,
    ``RETURN``) or extract nested blocks into keywords.

    Not analysed: keywords called from ``[Setup]`` / ``[Teardown]``, and run keywords nested inside conditional
    keywords (``Run Keyword If    $a    Run Keyword If    $b    ...``), where only the outer keyword counts.

    """

    name = "cognitive-complexity-keyword"
    rule_id = "CPX03"
    message = (
        "Keyword '{block_name}' has too high cognitive complexity ({complexity}/{allowed_complexity}), "
        "main contributors: {contributors}"
    )
    severity = RuleSeverity.WARNING
    enabled = False
    parameters = [
        RuleParam(name="max_complexity", default=15, converter=int, desc="allowed cognitive complexity"),
    ]
    severity_threshold = SeverityThreshold(
        "max_complexity", compare_method="greater", substitute_value="allowed_complexity"
    )
    added_in_version = "9.5.0"
    sonar_qube_attrs = COMPLEXITY_SONAR_QUBE_ATTRS
    fix_suggestion = COGNITIVE_FIX

    def check(self, node: Keyword, result: ComplexityResult) -> None:
        _report_if_too_complex(self, node, result.cognitive, self.max_complexity, result.cognitive_contributors)


class CognitiveComplexityTestCaseRule(Rule):
    """
    Test case or task has too high cognitive complexity.

    Same metric as ``cognitive-complexity-keyword``, for test cases and tasks. Tests are usually flatter than
    keywords, so the default limit is lower. Move nested logic into keywords so the test reads as a scenario.

    """

    name = "cognitive-complexity-test-case"
    rule_id = "CPX04"
    message = (
        "Test case '{block_name}' has too high cognitive complexity ({complexity}/{allowed_complexity}), "
        "main contributors: {contributors}"
    )
    severity = RuleSeverity.WARNING
    enabled = False
    parameters = [
        RuleParam(name="max_complexity", default=10, converter=int, desc="allowed cognitive complexity"),
    ]
    severity_threshold = SeverityThreshold(
        "max_complexity", compare_method="greater", substitute_value="allowed_complexity"
    )
    added_in_version = "9.5.0"
    sonar_qube_attrs = COMPLEXITY_SONAR_QUBE_ATTRS
    fix_suggestion = COGNITIVE_FIX

    def check(self, node: TestCase, result: ComplexityResult) -> None:
        _report_if_too_complex(self, node, result.cognitive, self.max_complexity, result.cognitive_contributors)
