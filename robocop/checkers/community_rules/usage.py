from dataclasses import dataclass, field
from typing import Dict, List, Optional

from robot.api import Token
from robot.parsing.model.blocks import Keyword

from robocop.checkers import ProjectChecker
from robocop.rules import Message, Rule, RuleSeverity
from robocop.utils.misc import normalize_robot_name
from robocop.utils.run_keywords import iterate_keyword_names

RULE_CATEGORY_ID = "01"

rules = {
    "10101": Rule(
        rule_id="10101",
        name="unused-keyword",
        msg="Keyword '{{ keyword_name }}' is not used",
        severity=RuleSeverity.WARNING,
        added_in_version="5.1.0",
        enabled=False,
        docs="""

        """,
    )
}


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
    name: str
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
    keywords: Dict[str, KeywordDefinition] = field(default_factory=dict)
    used_keywords: Dict[str, KeywordUsage] = field(default_factory=dict)

    @property
    def any_private(self):
        return any(keyword.is_private for keyword in self.keywords.values())

    @property
    def private_keywords(self):
        return [keyword for keyword in self.keywords.values() if keyword.is_private]

    @property
    def not_used_keywords(self):
        return [keyword for keyword in self.keywords.values() if not keyword.used]

    def search_usage(self):
        # TODO search in other files (imports) for non suites
        # TODO option to also report keyword only used in not used keywords ('Nested Not Used Keyword' from tests)
        # TODO below could be done inside robotfile? unless the access to others is required
        for normalized_name, keyword_usage in self.used_keywords.items():
            if normalized_name in self.keywords:
                self.keywords[normalized_name].update(keyword_usage)


class UnusedKeywords(ProjectChecker):
    reports = ("unused-keyword",)

    # TODO embedded
    # TODO ignore run keywords with variables?

    def __init__(self):
        self.files: Dict[str, RobotFile] = {}
        self.current_file: Optional[RobotFile] = None
        super().__init__()

    def scan_project(self) -> List["Message"]:
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

    def visit_File(self, node):  # noqa
        self.current_file = RobotFile(node.source)  # TODO handle "-"
        self.generic_visit(node)
        self.files[self.current_file.path] = self.current_file

    def visit_TestCaseSection(self, node):  # noqa
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

    def visit_Setup(self, node):  # noqa
        self.mark_used_keywords(node, Token.NAME)

    visit_TestTeardown = visit_SuiteTeardown = visit_Teardown = visit_TestSetup = visit_SuiteSetup = visit_Setup

    def visit_Template(self, node):  # noqa
        # allow / disallow param
        if node.value:
            name_token = node.get_token(Token.NAME)
            self.mark_used_keyword(node.value, name_token)
        self.generic_visit(node)

    visit_TestTemplate = visit_Template

    def visit_KeywordCall(self, node):  # noqa
        self.mark_used_keywords(node, Token.KEYWORD)

    def visit_Keyword(self, node):  # noqa
        # TODO handle robot:private
        name = node.name
        normalized_name = normalize_robot_name(name)
        self.current_file.keywords[normalized_name] = KeywordDefinition(name, node)
        self.generic_visit(node)
