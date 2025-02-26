from __future__ import annotations

from robot.api import Token

from robocop.linter.rules import Rule, RuleParam, RuleSeverity


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
