from __future__ import annotations

from robot.api import Token
from robot.parsing.model.blocks import Keyword, TestCase

from robocop.linter.rules import Rule, RuleParam, RuleSeverity, VisitorChecker


def parse_order_comma_sep_list(value: str, mapping: dict) -> list:
    ordered = []
    for item in value.split(","):
        item_lower = item.lower()
        if item_lower not in mapping:
            raise ValueError(f"Invalid value: {item}. Supported values: {', '.join(mapping.keys())}")
        ordered.append(mapping[item_lower])
    return ordered


def parse_keyword_order_param(value: str) -> list:
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


def parse_test_case_order_param(value: str) -> list:
    mapping = {
        "documentation": Token.DOCUMENTATION,
        "tags": Token.TAGS,
        "timeout": Token.TIMEOUT,
        "setup": Token.SETUP,
        "template": Token.TEMPLATE,
        "keyword": Token.KEYWORD,
        "teardown": Token.TEARDOWN,
    }
    return parse_order_comma_sep_list(value, mapping)


def configure_sections_order(value):
    section_map = {
        "settings": Token.SETTING_HEADER,
        "variables": Token.VARIABLE_HEADER,
        "testcase": Token.TESTCASE_HEADER,
        "testcases": Token.TESTCASE_HEADER,
        "task": "TASK HEADER",
        "tasks": "TASK HEADER",
        "keyword": Token.KEYWORD_HEADER,
        "keywords": Token.KEYWORD_HEADER,
    }
    sections_order = {}
    for index, name in enumerate(value.split(",")):
        if name.lower() not in section_map or section_map[name.lower()] in sections_order:
            raise ValueError(f"Invalid section name: `{name}`")
        sections_order[section_map[name.lower()]] = index
    if Token.TESTCASE_HEADER in sections_order:
        sections_order["TASK HEADER"] = sections_order[Token.TESTCASE_HEADER]
    return sections_order


class TestCaseSectionOutOfOrderRule(Rule):
    """
    Settings or body in test case are out of order.

    Sections should be defined in order set by ``sections_order`` parameter.
    Default order: ``documentation,tags,timeout,setup,template,keyword,teardown``.

    To change the default order use following option::

        robocop check --configure test-case-section-out-of-order.sections_order=comma,separated,list,of,sections

    where section should be case-insensitive name from the list:

    - documentation
    - tags
    - timeout
    - setup
    - template
    - keyword
    - teardown

    Order of not configured sections is ignored.

    Incorrect code example::

        *** Test Cases ***
        Keyword After Teardown
            [Documentation]    This is test Documentation
            [Tags]    tag1    tag2
            [Teardown]    Log    abc
            Keyword1

    Correct code::

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
            default="documentation,tags,timeout,setup,template,keyword,teardown",
            converter=parse_test_case_order_param,
            show_type="str",
            desc="order of sections in comma-separated list",
        ),
    ]
    added_in_version = "5.3.0"
    style_guide_ref = ["#test-cases-or-tasks"]


class KeywordSectionOutOfOrderRule(Rule):
    """
    Settings or body in keyword are out of order.

    Sections should be defined in order set by ``sections_order`` parameter.
    Default order: ``documentation,tags,arguments,timeout,setup,keyword,teardown``.

    To change the default order use following option::

        robocop check --configure keyword-section-out-of-order.sections_order=comma,separated,list,of,sections

    where section should be case-insensitive name from the list:
    documentation, tags, arguments, timeout, setup, keyword, teardown.
    Order of not configured sections is ignored.

    Incorrect code example::

        *** Keywords ***
        Keyword After Teardown
            [Tags]    tag1    tag2
            [Teardown]    Log    abc
            Keyword1
            [Documentation]    This is keyword Documentation

    Correct code example::

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


class SectionOutOfOrderRule(Rule):
    """
    Section does not follow recommended order.

    It's advised to use consistent section orders for readability.

    Default order: ``comments,settings,variables,testcases,keywords``.

    To change the default order use following option::

        robocop check --configure section-out-of-order.sections_order=comma,separated,list,of,sections

    Order of not configured sections is ignored.

    Incorrect code example::

        *** Settings ***

        *** Keywords ***

        *** Test Cases ***

    Correct code::

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


class TestAndKeywordOrderChecker(VisitorChecker):
    test_case_section_out_of_order: TestCaseSectionOutOfOrderRule
    keyword_section_out_of_order: KeywordSectionOutOfOrderRule

    def __init__(self):
        self.rules_by_node_type = {}
        self.expected_order = {}
        super().__init__()

    def visit_File(self, node) -> None:  # noqa: N802
        self.rules_by_node_type = {
            Keyword: self.keyword_section_out_of_order,
            TestCase: self.test_case_section_out_of_order,
        }
        self.expected_order = {
            Keyword: self.keyword_section_out_of_order.sections_order,
            TestCase: self.test_case_section_out_of_order.sections_order,
        }
        self.generic_visit(node)

    def check_order(self, node) -> None:
        max_order_indicator = -1
        for subnode in node.body:
            try:
                subnode_type = subnode.type
            except AttributeError:
                continue
            if subnode_type not in self.expected_order[type(node)]:
                continue
            this_node_expected_order = self.expected_order[type(node)].index(subnode.type)
            if this_node_expected_order < max_order_indicator:
                error_node = subnode.data_tokens[0]
                self.report(
                    self.rules_by_node_type[type(node)],
                    section_name=subnode_type,
                    recommended_order=", ".join(self.expected_order[type(node)]),
                    node=error_node,
                    col=error_node.col_offset + 1,
                    end_col=error_node.end_col_offset + 1,
                )
            else:
                max_order_indicator = this_node_expected_order

    visit_Keyword = visit_TestCase = check_order  # noqa: N815
