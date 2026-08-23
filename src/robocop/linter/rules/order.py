from __future__ import annotations

from typing import TYPE_CHECKING, Any

from robot.api import Token

from robocop.linter import sonar_qube
from robocop.linter.rules import Rule, RuleParam, RuleSeverity

if TYPE_CHECKING:
    from robot.parsing.model.blocks import Keyword, TestCase
    from robot.parsing.model.statements import SectionHeader


def report_out_of_order_settings(rule: Rule, node: Keyword | TestCase) -> None:
    """Report ``rule`` for every setting or body item that breaks the expected order."""
    expected_order = rule.sections_order
    max_order_indicator = -1
    for subnode in node.body:
        try:
            subnode_type = subnode.type
        except AttributeError:
            continue
        if subnode_type not in expected_order:
            continue
        this_node_expected_order = expected_order.index(subnode_type)
        if this_node_expected_order < max_order_indicator:
            error_node = subnode.data_tokens[0]
            rule.report(
                section_name=subnode_type,
                recommended_order=", ".join(expected_order),
                node=error_node,
                col=error_node.col_offset + 1,
                end_col=error_node.end_col_offset + 1,
            )
        else:
            max_order_indicator = this_node_expected_order


def parse_order_comma_sep_list(value: str, mapping: dict[str, Any]) -> list[str]:
    ordered = []
    for item in value.split(","):
        item_lower = item.lower()
        if item_lower not in mapping:
            raise ValueError(f"Invalid value: {item}. Supported values: {', '.join(mapping.keys())}")
        ordered.append(mapping[item_lower])
    return ordered


def parse_keyword_order_param(value: str) -> list[str]:
    mapping = {
        "documentation": Token.DOCUMENTATION,
        "tags": Token.TAGS,
        "arguments": Token.ARGUMENTS,
        "timeout": Token.TIMEOUT,
        "setup": Token.SETUP,
        "keyword": Token.KEYWORD,
        "teardown": Token.TEARDOWN,
    }
    return parse_order_comma_sep_list(value, mapping)


def parse_test_case_order_param(value: str) -> list[str]:
    mapping = {
        "documentation": Token.DOCUMENTATION,
        "metadata": Token.METADATA,
        "tags": Token.TAGS,
        "timeout": Token.TIMEOUT,
        "setup": Token.SETUP,
        "template": Token.TEMPLATE,
        "keyword": Token.KEYWORD,
        "teardown": Token.TEARDOWN,
    }
    return parse_order_comma_sep_list(value, mapping)


def configure_sections_order(value: str) -> dict[str, int]:
    section_map: dict[str, str] = {
        "comments": Token.COMMENT_HEADER,
        "settings": Token.SETTING_HEADER,
        "variables": Token.VARIABLE_HEADER,
        "testcase": Token.TESTCASE_HEADER,
        "testcases": Token.TESTCASE_HEADER,
        "task": "TASK HEADER",
        "tasks": "TASK HEADER",
        "keyword": Token.KEYWORD_HEADER,
        "keywords": Token.KEYWORD_HEADER,
    }
    sections_order: dict[str, int] = {}
    for index, name in enumerate(value.split(",")):
        if name.lower() not in section_map or section_map[name.lower()] in sections_order:
            raise ValueError(f"Invalid section name: `{name}`")
        sections_order[section_map[name.lower()]] = index
    if Token.TESTCASE_HEADER in sections_order:
        sections_order["TASK HEADER"] = sections_order[Token.TESTCASE_HEADER]
    return sections_order


class TestCaseSectionOutOfOrderRule(Rule):
    """
    Settings or body in the test case are out of order.

    Sections should be defined in order set by the ``sections_order`` parameter.
    Default order: ``documentation,metadata,tags,timeout,setup,template,keyword,teardown``.

    To change the default order, use the following option:

        robocop check --configure test-case-section-out-of-order.sections_order=comma,separated,list,of,sections

    where section should be a case-insensitive name from the list:

    - documentation
    - metadata
    - tags
    - timeout
    - setup
    - template
    - keyword
    - teardown

    Order of not configured sections is ignored.

    ``metadata`` refers to the test case ``[Metadata]`` setting, which requires Robot Framework 7.5 or newer.

    Incorrect code example:

        *** Test Cases ***
        Keyword After Teardown
            [Documentation]    This is test Documentation
            [Tags]    tag1    tag2
            [Teardown]    Log    abc
            Keyword1

    Correct code:

        *** Test Cases ***
        Keyword After Teardown
            [Documentation]    This is test Documentation
            [Tags]    tag1    tag2
            Keyword1
            [Teardown]    Log    abc

    """

    name = "test-case-section-out-of-order"
    rule_id = "ORD01"
    message = (
        "'{section_name}' is in wrong place of Test Case. "
        "Recommended order of elements in Test Cases: {recommended_order}"
    )
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(
            name="sections_order",
            default="documentation,metadata,tags,timeout,setup,template,keyword,teardown",
            converter=parse_test_case_order_param,
            show_type="str",
            desc="order of sections in comma-separated list",
        ),
    ]
    added_in_version = "5.3.0"
    style_guide_ref = ["#test-cases-or-tasks"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0927",)

    def check(self, node: TestCase) -> None:
        if not self.enabled:
            return
        report_out_of_order_settings(self, node)


class KeywordSectionOutOfOrderRule(Rule):
    """
    Settings or body in keyword are out of order.

    Sections should be defined in order set by the ``sections_order`` parameter.
    Default order: ``documentation,tags,arguments,timeout,setup,keyword,teardown``.

    To change the default order use following option:

        robocop check --configure keyword-section-out-of-order.sections_order=comma,separated,list,of,sections

    where section should be case-insensitive name from the list:
    documentation, tags, arguments, timeout, setup, keyword, teardown.
    Order of not configured sections is ignored.

    Incorrect code example:

        *** Keywords ***
        Keyword After Teardown
            [Tags]    tag1    tag2
            [Teardown]    Log    abc
            Keyword1
            [Documentation]    This is keyword Documentation

    Correct code example:

        *** Keywords ***
        Keyword After Teardown
            [Documentation]    This is keyword Documentation
            [Tags]    tag1    tag2
            Keyword1
            [Teardown]    Log    abc

    """

    name = "keyword-section-out-of-order"
    rule_id = "ORD02"
    message = (
        "'{section_name}' is in wrong place of Keyword. Recommended order of elements in Keyword: {recommended_order}"
    )
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(
            name="sections_order",
            default="documentation,tags,arguments,timeout,setup,keyword,teardown",
            converter=parse_keyword_order_param,
            show_type="str",
            desc="order of sections in comma-separated list",
        ),
    ]
    added_in_version = "5.3.0"
    style_guide_ref = ["#keyword"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0928",)

    def check(self, node: Keyword) -> None:
        if not self.enabled:
            return
        report_out_of_order_settings(self, node)


class SectionOutOfOrderRule(Rule):
    """
    Section does not follow the recommended order.

    It's advised to use consistent section orders for readability.

    Default order: ``comments,settings,variables,testcases,keywords``.

    To change the default order, use the following option:

        robocop check --configure section-out-of-order.sections_order=comma,separated,list,of,sections

    The order of not configured sections is ignored.

    Incorrect code example:

        *** Settings ***

        *** Keywords ***

        *** Test Cases ***

    Correct code:

        *** Settings ***

        *** Test Cases ***

        *** Keywords ***

    """

    name = "section-out-of-order"
    rule_id = "ORD03"
    message = "'{section_name}' section header is defined in wrong order: {recommended_order}"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    parameters = [
        RuleParam(
            name="sections_order",
            default="settings,variables,testcases,keywords",
            converter=configure_sections_order,
            show_type="str",
            desc="order of sections in comma-separated list",
        )
    ]
    style_guide_ref = ["#sections"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0809",)

    def check(self, node: SectionHeader, previous_order_ids: list[int], order_id: int) -> None:
        if not self.enabled or not any(previous_id > order_id for previous_id in previous_order_ids):
            return
        token = node.data_tokens[0]
        self.report(
            section_name=token.value,
            recommended_order=self.section_order_to_str(self.sections_order),
            node=node,
            end_col=token.end_col_offset + 1,
        )

    @staticmethod
    def section_order_to_str(order: dict[str, int]) -> str:
        by_index = sorted(order.items(), key=lambda x: x[1])
        name_map = {
            Token.COMMENT_HEADER: "Comments",
            Token.SETTING_HEADER: "Settings",
            Token.VARIABLE_HEADER: "Variables",
            Token.TESTCASE_HEADER: "Test Cases / Tasks",
            "TASK HEADER": "Test Cases / Tasks",
            Token.KEYWORD_HEADER: "Keywords",
        }
        order_str: list[str] = []
        for name, _ in by_index:
            mapped_name = name_map[name]
            if mapped_name not in order_str:
                order_str.append(mapped_name)
        return " > ".join(order_str)
