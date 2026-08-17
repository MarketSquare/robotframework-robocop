"""Checkers for the rules defined in ``robocop.linter.rules.tags``."""

from __future__ import annotations

import ast
from collections import defaultdict
from typing import TYPE_CHECKING

from robot.api import Token
from robot.api.parsing import ModelVisitor
from robot.model.tags import TagPatterns
from robot.parsing.model.blocks import Keyword, KeywordSection, SettingSection
from robot.parsing.model.statements import LibraryImport, ResourceImport, Statement, TemplateArguments
from robot.utils import unescape
from robot.variables.search import search_variable

from robocop.linter.rules import VisitorChecker, tags
from robocop.linter.rules.tags import TagNode, new_tag_token, split_tag_on_variables
from robocop.linter.utils.misc import normalize_robot_name
from robocop.parsing.run_keywords import (
    is_run_keyword,
    iterate_keyword_calls,
    parse_run_keyword_calls,
    resolve_run_keyword,
)
from robocop.parsing.variables import VariableMatches  # type: ignore[attr-defined]
from robocop.version_handling import ROBOT_VERSION

if TYPE_CHECKING:
    from collections.abc import Iterable

    from robot.parsing import File
    from robot.parsing.model.blocks import TestCase
    from robot.parsing.model.statements import (
        DefaultTags,
        Documentation,
        ForceTags,
        KeywordCall,
        KeywordTags,
        Setup,
        Tags,
        Template,
        TestTemplate,
    )

    from robocop.parsing.run_keywords import KeywordCallTokens

RUNTIME_IMPORT_KEYWORDS = {
    "importlibrary",
    "importresource",
    "builtin.importlibrary",
    "builtin.importresource",
}
RUNTIME_IMPORT_DISPATCH_KEYWORDS = {
    "builtin.callmethod",
    "builtin.evaluate",
    "callmethod",
    "evaluate",
}
RUNTIME_IMPORT_OR_DISPATCH_KEYWORDS = RUNTIME_IMPORT_KEYWORDS | RUNTIME_IMPORT_DISPATCH_KEYWORDS


class RuntimeImportFinder(ModelVisitor):  # type: ignore[misc]
    """Find runtime imports that may introduce BuiltIn keyword shadows."""

    def __init__(
        self,
        suite_template: Token | None,
    ) -> None:
        self.suite_template = suite_template
        self.found = False

    @staticmethod
    def is_runtime_import_or_uncertain(name: str) -> bool:
        if search_variable(name, ignore_errors=True).base:
            return True
        unescaped_name = unescape(name)
        words = unescaped_name.split()
        return any(
            normalize_robot_name(" ".join(words[index:])) in RUNTIME_IMPORT_OR_DISPATCH_KEYWORDS
            for index in range(len(words))
        )

    @staticmethod
    def argument_can_execute_import(value: str) -> bool:
        normalized_value = normalize_robot_name(unescape(value))
        if "importresource" in normalized_value or "importlibrary" in normalized_value:
            return True
        return any(
            match.identifier == "$"
            and (str(match.base).startswith("{") or any(marker in str(match.base) for marker in (".", "(", "[")))
            for match in VariableMatches(value, ignore_errors=True)
        )

    def check_calls(self, calls: Iterable[KeywordCallTokens]) -> None:
        for call in calls:
            has_list_expansion = resolve_run_keyword(call.name.value, allow_bdd_prefixes=True) and any(
                search_variable(argument.value, ignore_errors=True).identifier == "@" for argument in call.arguments
            )
            if (
                has_list_expansion
                or self.is_runtime_import_or_uncertain(call.name.value)
                or any(self.argument_can_execute_import(argument.value) for argument in call.arguments)
            ):
                self.found = True
                return

    def check(self, node: KeywordCall | Setup | Template, name_token_type: str) -> None:
        self.check_calls(
            iterate_keyword_calls(
                node,
                name_token_type,
                allow_bdd_prefixes=True,
            )
        )

    def visit_KeywordCall(self, node: KeywordCall) -> None:  # noqa: N802
        self.check(node, Token.KEYWORD)

    def visit_Setup(self, node: Setup) -> None:  # noqa: N802
        self.check(node, Token.NAME)

    visit_Teardown = visit_Setup  # noqa: N815
    visit_SuiteSetup = visit_Setup  # noqa: N815
    visit_SuiteTeardown = visit_Setup  # noqa: N815
    visit_TestSetup = visit_Setup  # noqa: N815
    visit_TestTeardown = visit_Setup  # noqa: N815

    def visit_Template(self, node: Template) -> None:  # noqa: N802
        self.check(node, Token.NAME)

    def visit_TestTemplate(self, node: TestTemplate) -> None:  # noqa: N802
        self.suite_template = node.get_token(Token.NAME)
        self.check(node, Token.NAME)

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        local_template = next((statement for statement in node.body if statement.type == Token.TEMPLATE), None)
        template = self.suite_template if local_template is None else local_template.get_token(Token.NAME)
        if template is not None and normalize_robot_name(template.value) != "none":
            for statement in node.body:
                if not isinstance(statement, TemplateArguments):
                    continue
                self.check_calls(
                    parse_run_keyword_calls(
                        [template, *statement.data_tokens],
                        allow_bdd_prefixes=True,
                    )
                )
        self.generic_visit(node)


class TagsChecker(VisitorChecker):
    """Checker for tag names, tag scopes and keyword tags."""

    tag_with_space: tags.TagWithSpaceRule
    tag_with_or_and: tags.TagWithOrAndRule
    tag_with_reserved_word: tags.TagWithReservedWordRule
    duplicated_tags: tags.DuplicatedTagsRule
    could_be_test_tags: tags.CouldBeTestTagsRule
    tag_already_set_in_test_tags: tags.TagAlreadySetInTestTagsRule
    unnecessary_default_tags: tags.UnnecessaryDefaultTagsRule
    empty_tags: tags.EmptyTagsRule
    could_be_keyword_tags: tags.CouldBeKeywordTagsRule
    tag_already_set_in_keyword_tags: tags.TagAlreadySetInKeywordTagsRule
    redundant_continue_on_failure: tags.RedundantContinueOnFailureRule
    # TODO: too many tags rule

    def __init__(self) -> None:
        self.in_keyword = False
        self.in_keywords = False
        self.tags_in_tests: list[list[str]] = []
        self.tags_in_keywords: list[list[str]] = []
        self.test_tags: set[str] = set()
        self.default_tags: set[str] = set()
        self.keyword_tags: set[str] = set()
        self.test_tags_node: ForceTags | None = None
        self.default_tags_node: DefaultTags | None = None
        self.keyword_tags_node: KeywordTags | None = None
        self.test_cases_count = 0
        self.keywords_count = 0
        self.suite_default_tags = False
        self.continue_on_failure_tag: str | None = None
        self.allow_unqualified_run_keywords = True
        self.allow_qualified_run_keywords = True
        self.in_templated_test = False
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.tags_in_tests = []
        self.tags_in_keywords = []
        self.test_tags = set()
        self.default_tags = set()
        self.keyword_tags = set()
        self.test_tags_node = None
        self.keyword_tags_node = None
        self.test_cases_count = 0
        self.keywords_count = 0
        self.suite_default_tags = self.has_default_tags(node)
        self.collect_file_context(node)
        super().visit_File(node)
        self.check_common_test_tags(node)
        self.check_common_keyword_tags(node)

    def collect_file_context(self, node: File) -> None:
        """Collect tags and possible BuiltIn keyword shadows before visiting sections."""
        self.allow_unqualified_run_keywords = True
        self.allow_qualified_run_keywords = True
        suite_template: Token | None = None
        keyword_tags_token = getattr(Token, "KEYWORD_TAGS", "KEYWORD TAGS")
        for section in node.sections:
            if isinstance(section, SettingSection):
                for statement in section.body:
                    if not statement.data_tokens:
                        continue
                    tag_names = {token.value for token in statement.data_tokens[1:]}
                    if statement.type == Token.FORCE_TAGS:
                        self.test_tags = tag_names
                    elif statement.type == Token.DEFAULT_TAGS:
                        self.default_tags = tag_names
                    elif statement.type == keyword_tags_token:
                        self.keyword_tags = tag_names
                    elif statement.type == Token.TEST_TEMPLATE:
                        suite_template = statement.get_token(Token.NAME)
                    elif isinstance(statement, (LibraryImport, ResourceImport)) or (
                        ROBOT_VERSION.major < 6 and statement.type == Token.ERROR
                    ):
                        self.allow_unqualified_run_keywords = False
                        self.allow_qualified_run_keywords = False
            elif isinstance(section, KeywordSection):
                for keyword in section.body:
                    if not isinstance(keyword, Keyword) or not keyword.name:
                        continue
                    if search_variable(keyword.name, ignore_errors=True).base:
                        self.allow_unqualified_run_keywords = False
                        self.allow_qualified_run_keywords = False
                    elif is_run_keyword(keyword.name):
                        self.allow_unqualified_run_keywords = False
                        if "." in normalize_robot_name(keyword.name):
                            self.allow_qualified_run_keywords = False
        runtime_import_finder = RuntimeImportFinder(
            suite_template,
        )
        runtime_import_finder.visit(node)
        executable_import = any(
            runtime_import_finder.argument_can_execute_import(token.value)
            for child in ast.walk(node)
            if isinstance(child, Statement)
            for token in child.data_tokens
        )
        if runtime_import_finder.found or executable_import:
            self.allow_unqualified_run_keywords = False
            self.allow_qualified_run_keywords = False

    @staticmethod
    def has_default_tags(node: File) -> bool:
        """
        Check if the suite defines ``Default Tags`` with a value.

        Empty test case ``[Tags]`` is used to overwrite such setting and should not be removed.
        ``Default Tags`` is not allowed in the suite initialization file, so it is enough to look it up in the
        current file.
        """
        return any(
            statement.type == Token.DEFAULT_TAGS and len(statement.data_tokens) > 1
            for section in node.sections
            if isinstance(section, SettingSection)
            for statement in section.body
        )

    def check_common_test_tags(self, node: File) -> None:
        """Report tags shared by all tests only if every test in the suite defines its own tags."""
        if not self.tags_in_tests or len(self.tags_in_tests) != self.test_cases_count:
            return
        if self.default_tags:
            self.unnecessary_default_tags.check(node, self.default_tags_node)
        if self.test_cases_count < 2:
            return
        common_tags = set.intersection(*[set(tags) for tags in self.tags_in_tests]) - self.test_tags
        self.could_be_test_tags.check(node, common_tags, self.test_tags_node)

    def check_common_keyword_tags(self, node: File) -> None:
        """Report tags shared by all keywords only if every keyword in the suite defines its own tags."""
        if not self.tags_in_keywords or len(self.tags_in_keywords) != self.keywords_count:
            return
        if self.keywords_count < 2:
            return
        common_tags = set.intersection(*[set(tags) for tags in self.tags_in_keywords]) - self.keyword_tags
        self.could_be_keyword_tags.check(node, common_tags, self.keyword_tags_node)

    def visit_KeywordSection(self, node: KeywordSection) -> None:  # noqa: N802
        self.in_keywords = True
        self.generic_visit(node)
        self.in_keywords = False

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
        self.keywords_count += 1
        self.in_keyword = True
        effective_tags = self.effective_tags(self.keyword_tags, self.local_tags(node))
        self.continue_on_failure_tag = self.find_continue_on_failure_tag(effective_tags)
        self.generic_visit(node)
        self.continue_on_failure_tag = None
        self.in_keyword = False

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        self.test_cases_count += 1
        template = next((statement for statement in node.body if statement.type == Token.TEMPLATE), None)
        self.in_templated_test = (
            self.templated_suite
            if template is None
            else bool(template.data_tokens[1:] and template.data_tokens[1].value.upper() != "NONE")
        )
        local_tags = self.local_tags(node)
        inherited_tags = self.default_tags if local_tags is None else set()
        effective_tags = self.effective_tags(self.test_tags | inherited_tags, local_tags)
        self.continue_on_failure_tag = self.find_continue_on_failure_tag(effective_tags)
        self.generic_visit(node)
        self.continue_on_failure_tag = None
        self.in_templated_test = False

    @staticmethod
    def local_tags(node: Keyword | TestCase) -> set[str] | None:
        tag_node = next((statement for statement in node.body if statement.type == Token.TAGS), None)
        if tag_node is None:
            return None
        return {token.value for token in tag_node.data_tokens[1:]}

    @staticmethod
    def effective_tags(inherited_tags: set[str], local_tags: set[str] | None) -> set[str]:
        if local_tags is None:
            return inherited_tags
        removal_patterns = TagPatterns(tag[1:] for tag in local_tags if tag.startswith("-") and len(tag) > 1)
        effective_tags = inherited_tags | {tag for tag in local_tags if not tag.startswith("-")}
        return {tag for tag in effective_tags if not removal_patterns.match(tag)}

    @staticmethod
    def find_continue_on_failure_tag(tag_names: set[str]) -> str | None:
        continue_on_failure_tags = (
            "robot:recursive-continue-on-failure",
            "robot:continue-on-failure",
        )
        for expected_tag in continue_on_failure_tags:
            matching_tags = sorted(tag for tag in tag_names if tag.lower().replace(" ", "") == expected_tag)
            if matching_tags:
                return matching_tags[0]
        return None

    def visit_KeywordCall(self, node: KeywordCall) -> None:  # noqa: N802
        if self.in_templated_test:
            return
        self.redundant_continue_on_failure.check(
            node,
            self.continue_on_failure_tag,
            self.allow_unqualified_run_keywords,
            self.allow_qualified_run_keywords,
        )

    def visit_ForceTags(self, node: ForceTags) -> None:  # noqa: N802
        self.test_tags = {token.value for token in node.data_tokens[1:]}
        self.test_tags_node = node
        self.check_tag_names(node)

    def visit_DefaultTags(self, node: DefaultTags) -> None:  # noqa: N802
        self.default_tags = {token.value for token in node.data_tokens[1:]}
        self.default_tags_node = node
        self.check_tag_names(node)

    def visit_KeywordTags(self, node: KeywordTags) -> None:  # noqa: N802
        self.keyword_tags = {token.value for token in node.data_tokens[1:]}
        self.keyword_tags_node = node
        self.check_tag_names(node)

    def visit_Tags(self, node: Tags) -> None:  # noqa: N802
        self.check_tag_names(node)
        self.empty_tags.check(node, self.in_keywords, not self.in_keywords and self.suite_default_tags)
        tags = [tag.value for tag in node.data_tokens[1:] if not tag.value.startswith("robot:")]
        if self.in_keywords:
            self.tags_in_keywords.append(tags)
            self.tag_already_set_in_keyword_tags.check(node, self.keyword_tags, self.keyword_tags_node)
        else:
            self.tags_in_tests.append(tags)
            self.tag_already_set_in_test_tags.check(node, self.test_tags, self.test_tags_node, self.suite_default_tags)

    def visit_Documentation(self, node: Documentation) -> None:  # noqa: N802
        """
        Parse tags from last line of documentation.

        Tags can be defined as comma separated list - Tags: tag1, tag2 .
        """
        if not self.in_keyword:
            return
        *_, last_line = node.lines
        args = [tag for tag in last_line if tag.type == Token.ARGUMENT]
        if not args or not args[0].value.lower().startswith("tags:"):
            return
        duplicates = defaultdict(list)
        for index, token in enumerate(args):
            tags = token.value
            col_start = token.col_offset
            if index == 0:
                tags = tags[len("tags:") :]
                col_start += len("tags:")
            for tag in tags.split(","):
                stripped_tag = tag.strip()
                if not stripped_tag:
                    continue
                normalized = stripped_tag.lower().replace(" ", "")
                subtoken = new_tag_token(stripped_tag, token.lineno, col_start)
                col_start += len(tag) + 1  # 1 for ,
                duplicates[normalized].append(subtoken)
                self.check_tag(subtoken, node)
        self.duplicated_tags.check(duplicates, node)

    def check_tag_names(self, node: TagNode) -> None:
        tags: defaultdict[str, list[Token]] = defaultdict(list)
        for tag in node.data_tokens[1:]:
            normalized_tag = tag.value.lower().replace(" ", "")
            tags[normalized_tag].append(tag)
            self.check_tag(tag, node)
        self.duplicated_tags.check(tags, node)

    def check_tag(self, tag_token: Token, node: TagNode | Documentation) -> None:
        substrings, variable_found = split_tag_on_variables(tag_token.value)
        for substring in substrings:
            has_space = self.tag_with_space.check(substring, tag_token, node)
            has_or_and = self.tag_with_or_and.check(substring, tag_token, node)
            if has_space or has_or_and:
                break
        self.tag_with_reserved_word.check(tag_token, node, variable_found)
