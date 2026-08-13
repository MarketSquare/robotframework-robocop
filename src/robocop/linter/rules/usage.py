from __future__ import annotations

import re
from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING

from robot.running.arguments import EmbeddedArguments

from robocop.linter import sonar_qube
from robocop.linter.rules import Rule, RuleSeverity
from robocop.version_handling import ROBOT_VERSION

if TYPE_CHECKING:
    from collections.abc import Iterable

    from robot.parsing.model.blocks import File, Keyword


class UnusedKeywordRule(Rule):
    """
    Keyword is not used.

    Reports not used keywords.

    Example:

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

    """

    name = "unused-keyword"
    rule_id = "KW04"
    message = "Keyword '{keyword_name}' is not used"
    severity = RuleSeverity.INFO
    deprecated = True  # TODO: temporary deprecation
    enabled = False
    added_in_version = "5.3.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("10101",)


if ROBOT_VERSION.major < 6:
    KeywordEmbedded = EmbeddedArguments
else:
    KeywordEmbedded = EmbeddedArguments.from_name


@dataclass
class KeywordUsage:
    found_def: bool = False
    used: int = 0
    names: set[str] = field(default_factory=set)

    def update(self, name: str) -> None:
        self.used += 1
        self.names.add(name)


@dataclass
class KeywordDefinition:
    name: str | re.Pattern[str]
    keyword_node: Keyword
    used: int = 0
    used_names: set[str] = field(default_factory=set)
    is_private: bool = False

    def update(self, used_as: KeywordUsage) -> None:
        used_as.found_def = True
        self.used += used_as.used
        self.used_names.update(used_as.names)


@dataclass
class RobotFile:
    path: str
    ast_model: File
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

    def search_usage(self) -> None:
        # TODO: search in other files (imports) for non suites
        # TODO: option to also report keyword only used in not used keywords ('Nested Not Used Keyword' from tests)
        # TODO: below could be done inside robotfile? unless the access to others is required
        for normalized_name, keyword_usage in self.used_keywords.items():
            if normalized_name in self.normal_keywords:
                self.normal_keywords[normalized_name].update(keyword_usage)
            else:
                for name in keyword_usage.names:
                    for keyword_name, keyword_def in self.embedded_keywords.items():
                        if isinstance(keyword_def.name, re.Pattern) and keyword_def.name.match(name):
                            # not entirely correct since keyword usage could be two usages with the same normalized name
                            self.embedded_keywords[keyword_name].update(keyword_usage)
