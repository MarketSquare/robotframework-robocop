from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token

from robocop.config.parser import validate_regex
from robocop.formatter.utils.misc import normalize_name

if TYPE_CHECKING:
    from robot.parsing.model.statements import Comment, KeywordCall

    from robocop.config.schema import SkipConfig


class Skip:
    """Defines global skip conditions for each formatter."""

    def __init__(self, skip_config: SkipConfig) -> None:
        self.return_values = "return_values" in skip_config.skip
        self.documentation = "documentation" in skip_config.skip
        self.comments = "comments" in skip_config.skip
        self.block_comments = "block_comments" in skip_config.skip
        self.keyword_call_names = {normalize_name(name) for name in skip_config.keyword_call}
        self.keyword_call_pattern = {validate_regex(pattern) for pattern in skip_config.keyword_call_pattern}
        self.any_keword_call = self.check_any_keyword_call()
        self.skip_settings = self.parse_skip_settings(skip_config)
        self.skip_sections = set(skip_config.sections)

    @staticmethod
    def parse_skip_settings(skip_config: SkipConfig) -> set[str]:
        settings = {
            "settings",
            "arguments",
            "setup",
            "teardown",
            "timeout",
            "template",
            "return",
            "return_statement",
            "tags",
        }
        skip_settings = set()
        for setting in settings:
            if setting in skip_config.skip:
                skip_settings.add(setting)
        return skip_settings

    def check_any_keyword_call(self) -> bool:
        return bool(self.keyword_call_names or self.keyword_call_pattern)

    def keyword_call(self, node: KeywordCall) -> bool:
        if not getattr(node, "keyword", None):
            return False
        return self.keyword_call_name(node.keyword)

    def keyword_call_name(self, name: str) -> bool:
        if not self.any_keword_call:
            return False
        normalized = normalize_name(name)
        if normalized in self.keyword_call_names:
            return True
        return any(pattern.search(name) for pattern in self.keyword_call_pattern)

    def setting(self, name: str) -> bool:
        if not self.skip_settings:
            return False
        if "settings" in self.skip_settings:
            return True
        return name.lower() in self.skip_settings

    def comment(self, comment: Comment) -> bool:
        if self.comments:
            return True
        if not self.block_comments:
            return False
        return bool(comment.tokens) and comment.tokens[0].type == Token.COMMENT

    def section(self, name: str) -> bool:
        return name in self.skip_sections
