from collections.abc import Iterable
from dataclasses import dataclass, field
from itertools import chain
from re import Pattern
from typing import Optional, Union

from robot.api import Token
from robot.errors import DataError
from robot.parsing.model.blocks import Keyword
from robot.parsing.model.statements import Tags
from robot.running.arguments import EmbeddedArguments

from robocop.checkers import ProjectChecker
from robocop.rules import CommunityRule, Message, RuleSeverity
from robocop.utils.misc import ROBOT_VERSION, normalize_robot_name
from robocop.utils.run_keywords import iterate_keyword_names

RULE_CATEGORY_ID = "01"

rules = {
    "10101": CommunityRule(
        rule_id="10101",
        name="unused-keyword",
        msg="Keyword '{{ keyword_name }}' is not used",
        severity=RuleSeverity.INFO,
        added_in_version="5.3.0",
        enabled=False,
        docs="""
        Reports not used keywords.

        Example::

            *** Test Cases ***
            Test that only non used keywords are reported
                Used Keyword

            *** Keywords ***
            Not Used Keyword  # this keyword will be reported as not used
                [Arguments]    ${arg}
                Should Be True    ${arg}>50

        Rule is under development - may report false negatives or positives. Currently it does only support
        keywords from suites and private keywords. If the keyword is called dynamically (for example through variable)
        it will be not detected as used.
        """,
    )
}

if ROBOT_VERSION.major < 6:
    KeywordEmbedded = EmbeddedArguments
else:
    KeywordEmbedded = EmbeddedArguments.from_name


@dataclass
class KeywordUsage:
    found_def: bool = False
    used: int = 0
    names: set[str] = field(default_factory=set)

    def update(self, name: str):
        self.used += 1
        self.names.add(name)


@dataclass
class KeywordDefinition:
    name: Union[str, Pattern]
    keyword_node: Keyword
    used: int = 0
    used_names: set[str] = field(default_factory=set)
    is_private: bool = False

    def update(self, used_as: KeywordUsage):
        used_as.found_def = True
        self.used += used_as.used
        self.used_names.update(used_as.names)


@dataclass
class RobotFile:
    path: str
    is_suite: bool = False
    normal_keywords: dict[str, KeywordDefinition] = field(default_factory=dict)
    embedded_keywords: dict[str, KeywordDefinition] = field(default_factory=dict)
    used_keywords: dict[str, KeywordUsage] = field(default_factory=dict)

    @property
    def keywords(self) -> Iterable[KeywordDefinition]:
        return chain(self.normal_keywords.values(), self.embedded_keywords.values())

    @property
    def any_private(self) -> bool:
        return any(keyword.is_private for keyword in self.keywords)

    @property
    def private_keywords(self) -> list[KeywordDefinition]:
        return [keyword for keyword in self.keywords if keyword.is_private]

    @property
    def not_used_keywords(self) -> list[KeywordDefinition]:
        not_used = []
        for keyword in self.keywords:
            if keyword.used or not (self.is_suite or keyword.is_private):
                continue
            not_used.append(keyword)
        return not_used

    def search_usage(self):
        # TODO: search in other files (imports) for non suites
        # TODO: option to also report keyword only used in not used keywords ('Nested Not Used Keyword' from tests)
        # TODO: below could be done inside robotfile? unless the access to others is required
        for normalized_name, keyword_usage in self.used_keywords.items():
            if normalized_name in self.normal_keywords:
                self.normal_keywords[normalized_name].update(keyword_usage)
            else:
                for name in keyword_usage.names:
                    for keyword_name, keyword_def in self.embedded_keywords.items():
                        if keyword_def.name.match(name):
                            # not entirely correct since keyword usage could be two usages with the same normalized name
                            self.embedded_keywords[keyword_name].update(keyword_usage)


class UnusedKeywords(ProjectChecker):
    reports = ("unused-keyword",)

    # TODO: ignore run keywords with variables?
    # TODO: handle BDD

    def __init__(self):
        self.files: dict[str, RobotFile] = {}
        self.current_file: Optional[RobotFile] = None
        super().__init__()

    def scan_project(self) -> list["Message"]:
        self.issues = []
        for robot_file in self.files.values():
            if not (robot_file.is_suite or robot_file.any_private):
                continue
            robot_file.search_usage()
            for keyword in robot_file.not_used_keywords:
                name = keyword.keyword_node.name
                self.report(
                    "unused-keyword",
                    source=robot_file.path,
                    node=keyword.keyword_node,
                    keyword_name=name,
                    end_col=len(name) + 1,
                )
        return self.issues

    def visit_File(self, node):  # noqa: N802
        self.current_file = RobotFile(node.source)  # TODO: handle "-"
        self.generic_visit(node)
        self.files[self.current_file.path] = self.current_file

    def visit_TestCaseSection(self, node):  # noqa: N802
        self.current_file.is_suite = True
        self.generic_visit(node)

    def mark_used_keywords(self, node, name_token_type):
        for keyword in iterate_keyword_names(node, name_token_type):
            self.mark_used_keyword(keyword.value, keyword)

    def mark_used_keyword(self, name: str, keyword):
        if not name:
            return
        normalized_name = normalize_robot_name(name)
        if normalized_name not in self.current_file.used_keywords:
            self.current_file.used_keywords[normalized_name] = KeywordUsage()
        self.current_file.used_keywords[normalized_name].update(name)
        # what about possible library names? searching removes, but for sake of collecting

    def visit_Setup(self, node):  # noqa: N802
        self.mark_used_keywords(node, Token.NAME)

    visit_TestTeardown = visit_SuiteTeardown = visit_Teardown = visit_TestSetup = visit_SuiteSetup = visit_Setup  # noqa: N815

    def visit_Template(self, node):  # noqa: N802
        # allow / disallow param
        if node.value:
            name_token = node.get_token(Token.NAME)
            self.mark_used_keyword(node.value, name_token)
        self.generic_visit(node)

    visit_TestTemplate = visit_Template  # noqa: N815

    def visit_KeywordCall(self, node):  # noqa: N802
        self.mark_used_keywords(node, Token.KEYWORD)

    def visit_Keyword(self, node):  # noqa: N802
        try:
            embedded = KeywordEmbedded(node.name)
            if embedded and embedded.args:
                self.current_file.embedded_keywords[node.name] = KeywordDefinition(
                    embedded.name, node, is_private=self.is_keyword_private(node)
                )
            else:
                normalized_name = normalize_robot_name(node.name)
                self.current_file.normal_keywords[normalized_name] = KeywordDefinition(
                    node.name, node, is_private=self.is_keyword_private(node)
                )
        except DataError:
            pass
        self.generic_visit(node)

    @staticmethod
    def is_keyword_private(node):
        for statement in node.body:
            if isinstance(statement, Tags):
                for tag in statement.get_tokens(Token.ARGUMENT):
                    if tag.value == "robot:private":
                        return True
        return False
