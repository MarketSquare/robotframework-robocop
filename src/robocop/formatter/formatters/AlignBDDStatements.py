from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api.parsing import Token
from robot.parsing.model.statements import KeywordCall

from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.formatters import Formatter
from robocop.parsing.run_keywords import BDD_PREFIXES

if TYPE_CHECKING:
    from robot.parsing.model.blocks import File, TestCase, TestCaseSection


class AlignBDDStatements(Formatter):
    """
    Align BDD statements in the test case body.

    Keyword calls prefixed with the BDD reserved keywords (``Given``, ``When``, ``And``, ``But`` and ``Then``)
    are indented so the keyword names following the prefixes are aligned in a single column:

    ```robotframework
    *** Test Cases ***
    There can be only one
        Given there are 3 ninjas
          And there are more than one ninja alive
         When 2 ninjas meet, they will fight
         Then one ninja dies (but not me)
          And there is one ninja less alive
    ```

    The width of the column is calculated separately for every test case using the longest BDD prefix used in
    its body. Statements that do not start with the BDD prefix are not formatted.

    The statement with the longest BDD prefix keeps the normal indentation, and the remaining ones are padded
    with extra spaces. The indentation is configurable with the global ``--indent`` option.
    """

    ENABLED = False

    def __init__(self) -> None:
        super().__init__()
        self.bdd_prefixes: frozenset[str] = BDD_PREFIXES

    def visit_File(self, node: File) -> File:  # noqa: N802
        self.bdd_prefixes = self.get_bdd_prefixes()
        return self.generic_visit(node)

    def get_bdd_prefixes(self) -> frozenset[str]:
        """Get BDD prefixes for languages configured for the source file."""
        prefixes = getattr(self.languages, "bdd_prefixes", None)  # RF 6.0+
        if not prefixes:
            return BDD_PREFIXES
        return frozenset(prefix.title() for prefix in prefixes)

    @skip_section_if_disabled
    def visit_TestCaseSection(self, node: TestCaseSection) -> TestCaseSection:  # noqa: N802
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_TestCase(self, node: TestCase) -> TestCase:  # noqa: N802
        self.align_block(node, indent=1)
        return node

    def get_bdd_prefix(self, node: KeywordCall) -> str | None:
        """Return BDD prefix used at the start of the keyword call, if there is any."""
        if node.get_token(Token.ASSIGN):  # BDD prefix would not start the line
            return None
        name = node.get_token(Token.KEYWORD)
        if not name or not name.value:
            return None
        prefix = name.value.split(maxsplit=1)[0]
        return prefix if prefix.title() in self.bdd_prefixes else None

    def align_block(self, block: object, indent: int) -> None:
        """Align the body of the block and any of its branches (such as ELSE or EXCEPT)."""
        self.align_body(getattr(block, "body", []), indent)
        for branch_name in ("orelse", "next"):
            branch = getattr(block, branch_name, None)
            if branch is not None:
                self.align_block(branch, indent)

    def align_body(self, body: list[object], indent: int) -> None:
        bdd_calls: list[tuple[KeywordCall, int]] = []
        max_width = 0
        for item in body:
            if isinstance(item, KeywordCall):
                prefix = self.get_bdd_prefix(item)
                if prefix is not None:
                    bdd_calls.append((item, len(prefix)))
                    max_width = max(max_width, len(prefix))
            elif hasattr(item, "body"):
                self.align_block(item, indent + 1)
        for keyword_call, width in bdd_calls:
            self.align_statement(keyword_call, indent, max_width - width)

    def align_statement(self, node: KeywordCall, indent: int, extra_width: int) -> None:
        if self.disablers.is_node_disabled(self.__class__.__name__, node):
            return
        separator = node.tokens[0]
        if separator.type != Token.SEPARATOR:
            return
        separator.value = self.formatting_config.indent * indent + " " * extra_width
