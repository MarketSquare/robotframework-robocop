"""Checkers for the rules defined in ``robocop.linter.rules.usage``."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from robot.api import Token
from robot.errors import DataError
from robot.parsing.model.statements import Tags

from robocop.linter.rules import ProjectChecker, usage
from robocop.linter.rules.usage import KeywordDefinition, KeywordEmbedded, KeywordUsage, RobotFile
from robocop.linter.utils.misc import normalize_robot_name
from robocop.parsing.run_keywords import iterate_keyword_names
from robocop.source_file import SourceFile, VirtualSourceFile

if TYPE_CHECKING:
    from robot.parsing.model.blocks import File, Keyword, Section
    from robot.parsing.model.statements import KeywordCall, Setup, Statement, Template

    from robocop.config.manager import ConfigManager
    from robocop.linter.diagnostics import Diagnostic


class UnusedKeywords(ProjectChecker):
    unused_keyword: usage.UnusedKeywordRule
    current_file: RobotFile

    # TODO: ignore run keywords with variables?
    # TODO: handle BDD

    def __init__(self) -> None:
        self.files: dict[str, RobotFile] = {}
        super().__init__()

    def scan_project(
        self,
        project_source_file: SourceFile | VirtualSourceFile,
        config_manager: ConfigManager,  # noqa: ARG002
    ) -> list[Diagnostic]:
        self.issues = []
        for robot_file in self.files.values():
            if not (robot_file.is_suite or robot_file.any_private):
                continue
            robot_file.search_usage()
            local_file = SourceFile(path=Path(robot_file.path), config=project_source_file.config)
            for keyword in robot_file.not_used_keywords:
                name = keyword.keyword_node.name
                self.report(
                    self.unused_keyword,
                    source=local_file,
                    node=keyword.keyword_node,
                    keyword_name=name,
                    end_col=len(name) + 1,
                )
        return self.issues

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.current_file = RobotFile(str(node.source), node)  # TODO: handle "-"
        # self.generic_visit(node)
        self.files[self.current_file.path] = self.current_file

    def visit_TestCaseSection(self, _node: Section) -> None:  # noqa: N802
        self.current_file.is_suite = True
        # self.generic_visit(node)

    def mark_used_keywords(self, node: Statement, name_token_type: str) -> None:
        for keyword in iterate_keyword_names(node, name_token_type):
            self.mark_used_keyword(keyword.value)

    def mark_used_keyword(self, name: str) -> None:
        if not name:
            return
        normalized_name = normalize_robot_name(name)
        if normalized_name not in self.current_file.used_keywords:
            self.current_file.used_keywords[normalized_name] = KeywordUsage()
        self.current_file.used_keywords[normalized_name].update(name)
        # what about possible library names? searching removes, but for sake of collecting

    def visit_Setup(self, node: Setup) -> None:  # noqa: N802
        self.mark_used_keywords(node, Token.NAME)

    visit_TestTeardown = visit_SuiteTeardown = visit_Teardown = visit_TestSetup = visit_SuiteSetup = visit_Setup  # noqa: N815

    def visit_Template(self, node: Template) -> None:  # noqa: N802
        # allow / disallow param
        if node.value:
            self.mark_used_keyword(node.value)
        # self.generic_visit(node)

    visit_TestTemplate = visit_Template  # noqa: N815

    def visit_KeywordCall(self, node: KeywordCall) -> None:  # noqa: N802
        self.mark_used_keywords(node, Token.KEYWORD)

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
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
        # self.generic_visit(node)

    @staticmethod
    def is_keyword_private(node: Keyword) -> bool:
        for statement in node.body:
            if isinstance(statement, Tags):
                for tag in statement.get_tokens(Token.ARGUMENT):
                    if tag.value == "robot:private":
                        return True
        return False
