from __future__ import annotations

import re
from re import Pattern

import click
from robot.api import Token
from robotidy.utils.misc import normalize_name


def parse_csv(value):
    if not value:
        return []
    return [val for val in value.split(",")]


def str_to_bool(value):
    return value.lower() == "true"


def validate_regex(value: str) -> Pattern | None:
    try:
        return re.compile(value)
    except re.error:
        raise ValueError(f"'{value}' is not a valid regular expression.") from None


class SkipConfig:
    """Skip configuration (global and for each transformer)."""

    # Following names will be taken from transformer config and provided to Skip class instead
    HANDLES = frozenset(
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

    def __init__(
        self,
        documentation: bool = False,
        return_values: bool = False,
        keyword_call: list | None = None,
        keyword_call_pattern: list | None = None,
        settings: bool = False,
        arguments: bool = False,
        setup: bool = False,
        teardown: bool = False,
        timeout: bool = False,
        template: bool = False,
        return_statement: bool = False,
        tags: bool = False,
        comments: bool = False,
        block_comments: bool = False,
        sections: str = "",
    ):
        self.documentation = documentation
        self.return_values = return_values
        self.keyword_call: list = keyword_call if keyword_call else []
        self.keyword_call_pattern: list = keyword_call_pattern if keyword_call_pattern else []
        self.settings = settings
        self.arguments = arguments
        self.setup = setup
        self.teardown = teardown
        self.timeout = timeout
        self.template = template
        self.return_statement = return_statement
        self.tags = tags
        self.comments = comments
        self.block_comments = block_comments
        self.sections = parse_csv(sections)

    def update_with_str_config(self, **kwargs):
        for name, value in kwargs.items():
            # find the value we're overriding and get its type from it
            original_value = self.__dict__[name]
            if isinstance(original_value, bool):
                self.__dict__[name] = str_to_bool(value)
            elif isinstance(original_value, list):
                parsed_list = parse_csv(value)
                self.__dict__[name].extend(parsed_list)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Skip:
    """Defines global skip conditions for each transformer."""

    def __init__(self, skip_config: SkipConfig):
        self.return_values = skip_config.return_values
        self.documentation = skip_config.documentation
        self.comments = skip_config.comments
        self.block_comments = skip_config.block_comments
        self.keyword_call_names = {normalize_name(name) for name in skip_config.keyword_call}
        self.keyword_call_pattern = {validate_regex(pattern) for pattern in skip_config.keyword_call_pattern}
        self.any_keword_call = self.check_any_keyword_call()
        self.skip_settings = self.parse_skip_settings(skip_config)
        self.skip_sections = set(skip_config.sections)

    @staticmethod
    def parse_skip_settings(skip_config):
        settings = {"settings", "arguments", "setup", "teardown", "timeout", "template", "return_statement", "tags"}
        skip_settings = set()
        for setting in settings:
            if getattr(skip_config, setting):
                skip_settings.add(setting)
        return skip_settings

    def check_any_keyword_call(self):
        return self.keyword_call_names or self.keyword_call_pattern

    def keyword_call(self, node):
        if not getattr(node, "keyword", None) or not self.any_keword_call:
            return False
        normalized = normalize_name(node.keyword)
        if normalized in self.keyword_call_names:
            return True
        for pattern in self.keyword_call_pattern:
            if pattern.search(node.keyword):
                return True
        return False

    def setting(self, name):
        if not self.skip_settings:
            return False
        if "settings" in self.skip_settings:
            return True
        return name.lower() in self.skip_settings

    def comment(self, comment):
        if self.comments:
            return True
        if not self.block_comments:
            return False
        return comment.tokens and comment.tokens[0].type == Token.COMMENT

    def section(self, name):
        return name in self.skip_sections


documentation_option = click.option("--skip-documentation", is_flag=True, help="Skip formatting of documentation")
return_values_option = click.option("--skip-return-values", is_flag=True, help="Skip formatting of return values")
keyword_call_option = click.option(
    "--skip-keyword-call", type=str, multiple=True, help="Keyword call name that should not be formatted"
)
keyword_call_pattern_option = click.option(
    "--skip-keyword-call-pattern",
    type=str,
    multiple=True,
    help="Keyword call name pattern that should not be formatted",
)
settings_option = click.option("--skip-settings", is_flag=True, help="Skip formatting of settings")
arguments_option = click.option("--skip-arguments", is_flag=True, help="Skip formatting of arguments")
setup_option = click.option("--skip-setup", is_flag=True, help="Skip formatting of setup")
teardown_option = click.option("--skip-teardown", is_flag=True, help="Skip formatting of teardown")
timeout_option = click.option("--skip-timeout", is_flag=True, help="Skip formatting of timeout")
template_option = click.option("--skip-template", is_flag=True, help="Skip formatting of template")
return_option = click.option("--skip-return", is_flag=True, help="Skip formatting of return statement")
tags_option = click.option("--skip-tags", is_flag=True, help="Skip formatting of tags")
sections_option = click.option(
    "--skip-sections",
    type=str,
    help="Skip formatting of sections. Provide multiple sections with comma separated value",
)
comments_option = click.option("--skip-comments", is_flag=True, help="Skip formatting of comments")
block_comments_option = click.option("--skip-block-comments", is_flag=True, help="Skip formatting of block comments")
option_group = {
    "name": "Skip formatting",
    "options": [
        "--skip-documentation",
        "--skip-return-values",
        "--skip-keyword-call",
        "--skip-keyword-call-pattern",
        "--skip-settings",
        "--skip-arguments",
        "--skip-setup",
        "--skip-teardown",
        "--skip-timeout",
        "--skip-template",
        "--skip-return",
        "--skip-tags",
        "--skip-comments",
        "--skip-block-comments",
        "--skip-sections",
    ],
}
