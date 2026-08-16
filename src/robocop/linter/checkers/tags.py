"""Checkers for the rules defined in ``robocop.linter.rules.tags``."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from robot.api import Token
from robot.parsing.model.blocks import SettingSection

from robocop.linter.rules import VisitorChecker, tags
from robocop.linter.rules.tags import TagNode, new_tag_token, split_tag_on_variables

if TYPE_CHECKING:
    from robot.parsing import File
    from robot.parsing.model.blocks import Keyword, KeywordSection, TestCase
    from robot.parsing.model.statements import (
        DefaultTags,
        Documentation,
        ForceTags,
        KeywordTags,
        Tags,
    )


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
        super().visit_File(node)
        self.check_common_test_tags(node)
        self.check_common_keyword_tags(node)

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
        self.generic_visit(node)
        self.in_keyword = False

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        self.test_cases_count += 1
        self.generic_visit(node)

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
            self.tag_already_set_in_test_tags.check(node, self.test_tags, self.test_tags_node)

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
        self.duplicated_tags.check(duplicates)

    def check_tag_names(self, node: TagNode) -> None:
        tags: defaultdict[str, list[Token]] = defaultdict(list)
        for tag in node.data_tokens[1:]:
            normalized_tag = tag.value.lower().replace(" ", "")
            tags[normalized_tag].append(tag)
            self.check_tag(tag, node)
        self.duplicated_tags.check(tags)

    def check_tag(self, tag_token: Token, node: TagNode | Documentation) -> None:
        substrings, variable_found = split_tag_on_variables(tag_token.value)
        for substring in substrings:
            has_space = self.tag_with_space.check(substring, tag_token, node)
            has_or_and = self.tag_with_or_and.check(substring, tag_token, node)
            if has_space or has_or_and:
                break
        self.tag_with_reserved_word.check(tag_token, node, variable_found)
