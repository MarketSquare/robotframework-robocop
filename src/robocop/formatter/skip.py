from __future__ import annotations

import re
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING

from robot.api import Token

from robocop.formatter.utils.misc import normalize_name

if TYPE_CHECKING:
    from robot.parsing.model.statements import Comment, KeywordCall


def validate_regex(value: str) -> re.Pattern[str]:
    try:
        return re.compile(value)
    except re.error:
        raise ValueError(f"'{value}' is not a valid regular expression.") from None


SKIP_OPTIONS = frozenset(
    {
        "skip_documentation",
        "skip_return_values",
        "skip_keyword_call",
        "skip_keyword_call_pattern",
        "skip_settings",
        "skip_arguments",
        "skip_setup",
        "skip_teardown",
        "skip_timeout",
        "skip_template",
        "skip_return_statement",
        "skip_tags",
        "skip_comments",
        "skip_block_comments",
        "skip_sections",
    }
)


@dataclass
class SkipConfig:
    skip: set[str] = field(default_factory=set)
    sections: set[str] = field(default_factory=set)
    keyword_call: set[str] = field(default_factory=set)
    keyword_call_pattern: set[str] = field(default_factory=set)

    @property
    def config_fields(self) -> set[str]:
        return {"skip", "skip_sections", "skip_keyword_call", "skip_keyword_call_pattern"}

    @classmethod
    def from_toml(cls, config: dict[str, list[str]]) -> SkipConfig:
        override = {
            "skip": config.get("skip", []),
            "sections": config.get("skip_sections", []),
            "keyword_call": config.get("skip_keyword_call", []),
            "keyword_call_pattern": config.get("skip_keyword_call_pattern", []),
        }
        return cls.from_lists(**override)

    @classmethod
    def from_lists(
        cls,
        skip: list[str] | None,
        sections: list[str] | None,
        keyword_call: list[str] | None,
        keyword_call_pattern: list[str] | None,
    ) -> SkipConfig:
        """
        Create instance of class from list-type arguments.

        Typer does not support sets yet, so we need to convert lists.
        """
        skip_set = set(skip) if skip is not None else set()
        sections_set = set(sections) if sections is not None else set()
        keyword_call_set = set(keyword_call) if keyword_call is not None else set()
        keyword_call_pattern_set = set(keyword_call_pattern) if keyword_call_pattern is not None else set()
        return cls(
            skip=skip_set,
            sections=sections_set,
            keyword_call=keyword_call_set,
            keyword_call_pattern=keyword_call_pattern_set,
        )

    def overwrite(self, other: SkipConfig) -> None:  # TODO refactor with config to not duplicate overwrite
        """
        Overwrite options loaded from configuration or default options with config from cli.

        If other has value set to None, it was never set and can be ignored.
        """
        for skip_field in fields(other):
            value = getattr(other, skip_field.name)
            if value is not None:
                setattr(self, skip_field.name, value)

    def update_with_str_config(self, **kwargs: str) -> None:
        for name, value in kwargs.items():
            if name == "keyword_call":
                self.keyword_call.update(value.split(","))
            elif name == "keyword_call_pattern":
                self.keyword_call_pattern.update(value.split(","))
            elif name == "sections":
                self.sections.update(value.split(","))
            elif value.lower() == "true":
                self.skip.add(name)
            else:
                self.skip.discard(name)


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
        return self.keyword_call_names or self.keyword_call_pattern

    def keyword_call(self, node: KeywordCall) -> bool:
        if not getattr(node, "keyword", None) or not self.any_keword_call:
            return False
        normalized = normalize_name(node.keyword)
        if normalized in self.keyword_call_names:
            return True
        return any(pattern.search(node.keyword) for pattern in self.keyword_call_pattern)

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
