"""
Complexity metrics for Robot Framework keywords and test cases.

Two metrics are computed from a single walk over the body of a keyword or test case:

* cyclomatic complexity (McCabe): ``1 + decision points``. ``IF``, ``ELSE IF``, ``FOR``, ``WHILE``, ``EXCEPT`` and
  each condition of a conditional BuiltIn keyword are decision points. ``and`` / ``or`` are not counted, which
  follows the ``mccabe`` / ruff ``C901`` convention.
* cognitive complexity (SonarSource, as interpreted by complexipy): structural constructs (``IF``, ``FOR``,
  ``WHILE``, ``EXCEPT``, conditional keywords) cost ``1 + nesting``, ``ELSE IF`` / ``ELSE`` / ``TRY ELSE`` cost a flat
  ``1``, and every run of like boolean operators in a condition costs ``1``. ``TRY`` bodies, ``FINALLY`` and
  ``GROUP`` add neither an increment nor nesting.

Every increment is recorded with its line, kind and nesting, so a score can be explained by its main contributors.
"""

from __future__ import annotations

import ast
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from robot.api import Token
from robot.parsing.model.blocks import For, If, Try, While
from robot.parsing.model.statements import KeywordCall
from robot.variables import search_variable

from robocop.linter.utils.misc import normalize_robot_name
from robocop.parsing.run_keywords import remove_bdd_prefix

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from robot.parsing.model.blocks import Keyword, TestCase
    from robot.parsing.model.statements import Node

BOOLEAN_OPERATORS = frozenset({"and", "or"})
VARIABLE_PLACEHOLDER = "v"
EVALUATION_VARIABLE = re.compile(r"\$[^\W\d]\w*")  # ``$name`` syntax in Python expressions
ELSE_IF_MARKER = "ELSE IF"
ELSE_MARKER = "ELSE"
RUN_KEYWORD_IF = "runkeywordif"
SET_VARIABLE_IF = "setvariableif"
CONDITIONAL_KEYWORDS = {
    "continueforloopif": "Continue For Loop If",
    "exitforloopif": "Exit For Loop If",
    "passexecutionif": "Pass Execution If",
    "returnfromkeywordif": "Return From Keyword If",
    "runkeywordandreturnif": "Run Keyword And Return If",
    RUN_KEYWORD_IF: "Run Keyword If",
    "runkeywordunless": "Run Keyword Unless",
    SET_VARIABLE_IF: "Set Variable If",
    "skipif": "Skip If",
}
DEFAULT_CONTRIBUTORS = 3


@dataclass(frozen=True)
class Increment:
    """
    A single contribution to the complexity scores.

    ``nesting`` is set for structural increments, whose cognitive cost includes the nesting level.
    """

    lineno: int
    kind: str
    cognitive: int = 0
    cyclomatic: int = 0
    nesting: int | None = None

    @property
    def label(self) -> str:
        return f"{self.kind} at nesting {self.nesting}" if self.nesting else self.kind


@dataclass(frozen=True)
class ComplexityResult:
    """Complexity of one keyword or test case, with the increments that explain it."""

    increments: tuple[Increment, ...]

    @property
    def cyclomatic(self) -> int:
        return 1 + sum(increment.cyclomatic for increment in self.increments)

    @property
    def cognitive(self) -> int:
        return sum(increment.cognitive for increment in self.increments)

    def cyclomatic_contributors(self) -> str:
        """Decision points counted by kind, most frequent first: ``3 IF, 2 ELSE IF, 1 FOR``."""
        counts = Counter(increment.kind for increment in self.increments if increment.cyclomatic)
        return ", ".join(f"{count} {kind}" for kind, count in counts.most_common()) or "none"

    def cognitive_contributors(self, limit: int = DEFAULT_CONTRIBUTORS) -> str:
        """Lines that add the most cognitive complexity: ``line 16 +4 (inline IF at nesting 3), ...``."""
        lines: defaultdict[int, list[Increment]] = defaultdict(list)
        for increment in self.increments:
            if increment.cognitive:
                lines[increment.lineno].append(increment)
        ranked = sorted(lines.items(), key=lambda item: (-sum(inc.cognitive for inc in item[1]), item[0]))
        return (
            ", ".join(
                f"line {lineno} +{sum(inc.cognitive for inc in increments)} "
                f"({', '.join(inc.label for inc in increments)})"
                for lineno, increments in ranked[:limit]
            )
            or "none"
        )


def compute_complexity(node: Keyword | TestCase) -> ComplexityResult:
    """Compute cyclomatic and cognitive complexity of a keyword or test case."""
    return ComplexityResult(increments=tuple(_walk_body(node.body, nesting=0)))


def count_boolean_sequences(condition: str | None) -> int:
    """
    Count sequences of like boolean operators (``and`` / ``or``) in a Python-style condition.

    ``a and b and c`` is one sequence, ``a and b or c`` two. Each boolean expression is counted on its own, so
    ``(a and b) == (c and d)`` has two sequences. Robot Framework variables are replaced by a placeholder first,
    and operators inside string literals are ignored. A condition that cannot be parsed counts as 0.
    """
    if not condition:
        return 0
    try:
        tree = ast.parse(_replace_variables(condition).strip(), mode="eval")
    except (SyntaxError, ValueError):
        return 0
    nested = {id(value) for node in ast.walk(tree) if isinstance(node, ast.BoolOp) for value in node.values}
    return sum(
        _count_sequences(_boolean_operators(node))
        for node in ast.walk(tree)
        if isinstance(node, ast.BoolOp) and id(node) not in nested
    )


def _boolean_operators(node: ast.BoolOp) -> list[type[ast.boolop]]:
    """Return the operators of a boolean expression in source order, including directly nested expressions."""
    operators: list[type[ast.boolop]] = []
    for index, value in enumerate(node.values):
        if index:
            operators.append(type(node.op))
        if isinstance(value, ast.BoolOp):
            operators.extend(_boolean_operators(value))
    return operators


def _count_sequences(operators: list[type[ast.boolop]]) -> int:
    return sum(1 for index, operator in enumerate(operators) if index == 0 or operator != operators[index - 1])


def _replace_variables(text: str) -> str:
    parts: list[str] = []
    rest = text
    while (match := search_variable(rest, ignore_errors=True)).start != -1:
        parts.extend((rest[: match.start], VARIABLE_PLACEHOLDER))
        rest = match.after
    parts.append(rest)
    return EVALUATION_VARIABLE.sub(VARIABLE_PLACEHOLDER, "".join(parts))


def _walk_body(body: Iterable[Node], nesting: int) -> Iterator[Increment]:
    for child in body:
        yield from _walk(child, nesting)


def _walk(node: Node, nesting: int) -> Iterator[Increment]:
    if isinstance(node, If):
        yield from _walk_if(node, nesting)
    elif isinstance(node, Try):
        yield from _walk_body(node.body, nesting)  # the TRY body itself is not nested
        yield from _walk_try_branches(node.next, nesting)
    elif isinstance(node, (For, While)):
        yield from _walk_loop(node, nesting)
    elif isinstance(node, KeywordCall):
        yield from _walk_keyword_call(node, nesting)
    else:  # GROUP and other containers: no increment, no nesting
        yield from _walk_body(getattr(node, "body", ()), nesting)


def _boolean_increment(lineno: int, condition: str | None) -> Iterator[Increment]:
    if sequences := count_boolean_sequences(condition):
        yield Increment(lineno, "boolean operators", cognitive=sequences)


def _walk_if(node: If, nesting: int) -> Iterator[Increment]:
    label = "inline IF" if node.header.type == Token.INLINE_IF else "IF"
    yield Increment(node.lineno, label, cognitive=1 + nesting, cyclomatic=1, nesting=nesting)
    yield from _boolean_increment(node.lineno, node.condition)
    yield from _walk_body(node.body, nesting + 1)
    yield from _walk_if_branches(node.orelse, nesting)


def _walk_if_branches(first: If | None, nesting: int) -> Iterator[Increment]:
    # chains are walked with a loop: long ELSE IF chains must not depend on the recursion limit
    branch = first
    while branch is not None:
        is_else_if = branch.header.type == Token.ELSE_IF
        yield Increment(branch.lineno, branch.header.type, cognitive=1, cyclomatic=int(is_else_if))
        if is_else_if:
            yield from _boolean_increment(branch.lineno, branch.condition)
        yield from _walk_body(branch.body, nesting + 1)
        branch = branch.orelse


def _walk_try_branches(first: Try | None, nesting: int) -> Iterator[Increment]:
    # chains are walked with a loop: long EXCEPT chains must not depend on the recursion limit
    branch = first
    while branch is not None:
        kind = branch.header.type
        if kind == Token.EXCEPT:
            yield Increment(branch.lineno, "EXCEPT", cognitive=1 + nesting, cyclomatic=1, nesting=nesting)
            yield from _walk_body(branch.body, nesting + 1)
        elif kind == Token.ELSE:
            yield Increment(branch.lineno, "TRY ELSE", cognitive=1)
            yield from _walk_body(branch.body, nesting + 1)
        else:  # FINALLY always runs, so it is neither an increment nor nested
            yield from _walk_body(branch.body, nesting)
        branch = branch.next


def _walk_loop(node: For | While, nesting: int) -> Iterator[Increment]:
    yield Increment(node.lineno, node.header.type, cognitive=1 + nesting, cyclomatic=1, nesting=nesting)
    if isinstance(node, While):
        yield from _boolean_increment(node.lineno, node.condition)
    yield from _walk_body(node.body, nesting + 1)


def _walk_keyword_call(node: KeywordCall, nesting: int) -> Iterator[Increment]:
    """Count conditional BuiltIn keywords (``Run Keyword If``, ``Set Variable If``, ...) as IF statements."""
    name = _conditional_keyword_name(node.keyword)
    if name is None:
        return
    keyword = CONDITIONAL_KEYWORDS[name]
    args = node.args
    yield Increment(node.lineno, keyword, cognitive=1 + nesting, cyclomatic=1, nesting=nesting)
    yield from _boolean_increment(node.lineno, args[0] if args else None)
    if name == RUN_KEYWORD_IF:
        branches = _run_keyword_if_branches(args)
    elif name == SET_VARIABLE_IF:
        branches = _set_variable_if_branches(args)
    else:
        branches = ()
    for branch, condition in branches:
        yield Increment(node.lineno, f"{keyword} {branch}", cognitive=1, cyclomatic=int(branch == ELSE_IF_MARKER))
        yield from _boolean_increment(node.lineno, condition)


def _conditional_keyword_name(name: str | None) -> str | None:
    """
    Return the normalized name of a conditional BuiltIn keyword, or ``None``.

    Resolved like Robot Framework: the full name first, then the name without a BDD prefix.
    """
    if not name:
        return None
    for candidate in (name, remove_bdd_prefix(name)):
        normalized = normalize_robot_name(candidate, remove_prefix="builtin.")
        if normalized in CONDITIONAL_KEYWORDS:
            return normalized
    return None


def _run_keyword_if_branches(args: tuple[str, ...]) -> tuple[tuple[str, str | None], ...]:
    """
    Return the ``ELSE IF`` / ``ELSE`` branches of ``Run Keyword If`` with the condition of each ``ELSE IF``.

    Branches are split like Robot Framework does: after a condition and keyword name, the first ``ELSE IF`` starts a
    new branch, and only when no ``ELSE IF`` is left does the first ``ELSE`` start the last one. Later markers are
    arguments of the called keyword.
    """
    branches: list[tuple[str, str | None]] = []
    remaining = args[2:]
    while ELSE_IF_MARKER in remaining:
        index = remaining.index(ELSE_IF_MARKER)
        branches.append((ELSE_IF_MARKER, remaining[index + 1] if index + 1 < len(remaining) else None))
        remaining = remaining[index + 3 :]
    if ELSE_MARKER in remaining:
        branches.append((ELSE_MARKER, None))
    return tuple(branches)


def _set_variable_if_branches(args: tuple[str, ...]) -> tuple[tuple[str, str | None], ...]:
    """``Set Variable If  c1  v1  c2  v2  default``: each extra condition is an ELSE IF, a trailing value an ELSE."""
    extra_conditions = tuple((ELSE_IF_MARKER, args[index]) for index in range(2, 2 * (len(args) // 2), 2))
    has_default = len(args) > 2 and len(args) % 2 == 1
    return extra_conditions + (((ELSE_MARKER, None),) if has_default else ())
