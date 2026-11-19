"""Complexity checkers"""

from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter import sonar_qube
from robocop.linter.rules import Rule, RuleParam, RuleSeverity, SeverityThreshold
from robocop.linter.utils.misc import last_lineno
from robocop.linter.utils.nesting import find_deep_blocks

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
NESTING_FIX = "Flatten the block with guard clauses or extract it into a keyword."


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
    ``RETURN``) or extract nested blocks into keywords. To limit the nesting depth directly, see
    ``nesting-depth-keyword``.

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


def _report_deep_blocks(rule: Rule, node: Keyword | TestCase) -> None:
    """Report the outermost blocks of ``node`` that are nested deeper than ``rule.max_depth``."""
    if not rule.enabled:
        return
    for block in find_deep_blocks(node, rule.max_depth):
        header_token = block.node.header.get_token(block.token_type)
        rule.report(
            block_name=node.name,
            depth=block.depth,
            max_depth=rule.max_depth,
            path=block.path_text,
            node=header_token or block.node,
            col=header_token.col_offset + 1 if header_token else None,
            end_col=header_token.end_col_offset + 1 if header_token else None,
            extended_disablers=(block.node.lineno, last_lineno(block.node)),
            sev_threshold_value=block.depth,
        )


class NestingDepthKeywordRule(Rule):
    """
    Keyword has too deeply nested control flow.

    Reports the outermost ``IF``, ``FOR``, ``WHILE`` or ``TRY`` block that is nested deeper than ``max_depth``
    levels. The first block in a keyword is level 1:

        *** Keywords ***
        Process Orders
            FOR    ${order}    IN    @{orders}               # level 1
                IF    $order.pending                          # level 2
                    TRY                                       # level 3
                        IF    $order.priority                 # level 4 - reported when max_depth=3
                            Escalate    ${order}
                        END
                    EXCEPT
                        Log    Failed
                    END
                END
            END

    The message shows the path to the deepest level, for example ``FOR > IF > TRY > IF``. The depth comes from the
    structure of the code, not from the indentation, and:

    - ``ELSE IF``, ``ELSE``, ``EXCEPT``, ``TRY ELSE`` and ``FINALLY`` are branches of their block and stay on its
      level, so an ``IF`` with ten ``ELSE IF`` branches has depth 1,
    - inline ``IF`` (``IF    $x    RETURN``) and conditional keywords such as ``Run Keyword If`` and ``Skip If`` do
      not add a level. They hold a single statement and are the usual way to flatten nesting with guard clauses,
    - ``GROUP`` does not add a level, but blocks inside it are counted (see ``nested-group`` to limit groups),
    - keyword calls are not followed: the depth is measured inside a single keyword.

    Blocks nested inside a reported block are not reported again. Extract the reported block into a keyword or use
    guard clauses (``IF    ...    RETURN`` / ``CONTINUE``) to flatten it. See ``cognitive-complexity-keyword`` for a
    metric that sums up nesting instead of limiting it.

    """

    name = "nesting-depth-keyword"
    rule_id = "CPX05"
    message = "Keyword '{block_name}' is nested too deeply ({depth}/{max_depth}), nesting path: {path}"
    severity = RuleSeverity.WARNING
    enabled = False
    parameters = [
        RuleParam(
            name="max_depth",
            default=4,
            converter=int,
            desc="allowed nesting depth of IF, FOR, WHILE and TRY blocks",
        ),
    ]
    severity_threshold = SeverityThreshold("max_depth", compare_method="greater", substitute_value="max_depth")
    added_in_version = "9.5.0"
    sonar_qube_attrs = COMPLEXITY_SONAR_QUBE_ATTRS
    fix_suggestion = NESTING_FIX

    def check(self, node: Keyword) -> None:
        _report_deep_blocks(self, node)


class NestingDepthTestCaseRule(Rule):
    """
    Test case or task has too deeply nested control flow.

    Same metric as ``nesting-depth-keyword``, for test cases and tasks. Tests are usually flatter than keywords, so
    the default limit is lower. Move nested logic into keywords so the test reads as a scenario.

    """

    name = "nesting-depth-test-case"
    rule_id = "CPX06"
    message = "Test case '{block_name}' is nested too deeply ({depth}/{max_depth}), nesting path: {path}"
    severity = RuleSeverity.WARNING
    enabled = False
    parameters = [
        RuleParam(
            name="max_depth",
            default=3,
            converter=int,
            desc="allowed nesting depth of IF, FOR, WHILE and TRY blocks",
        ),
    ]
    severity_threshold = SeverityThreshold("max_depth", compare_method="greater", substitute_value="max_depth")
    added_in_version = "9.5.0"
    sonar_qube_attrs = COMPLEXITY_SONAR_QUBE_ATTRS
    fix_suggestion = NESTING_FIX

    def check(self, node: TestCase) -> None:
        _report_deep_blocks(self, node)
