from typing import Set

from robot.api import Token
from robot.utils.robottime import timestr_to_secs

from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleParam, RuleSeverity
from robocop.utils.misc import normalize_robot_name
from robocop.utils.run_keywords import iterate_keyword_names

RULE_CATEGORY_ID = "00"


def comma_separated_list(value: str) -> Set[str]:
    if value is None:
        return set()
    return {normalize_robot_name(kw) for kw in value.split(",")}


rules = {
    "10001": Rule(
        RuleParam(
            name="max_time", default=0, converter=timestr_to_secs, desc="Maximum amount of time allowed in Sleep"
        ),
        rule_id="10001",
        name="sleep-keyword-used",
        msg="Sleep keyword with '{{ duration_time }}' sleep time found",
        severity=RuleSeverity.WARNING,
        added_in_version="5.0.0",
        enabled=False,
        docs="""
        Avoid using Sleep keyword in favour of polling.
        
        For example::
        
            *** Keywords ***
            Add To Cart
                [Arguments]    ${item_name}
                Sleep    30s  # wait for page to load
                Element Should Be Visible    ${MAIN_HEADER}
                Click Element    //div[@name='${item_name}']/div[@id='add_to_cart']
        
        Can be rewritten to::
        
            *** Keywords ***
            Add To Cart
                [Arguments]    ${item_name}
                Wait Until Element Is Visible    ${MAIN_HEADER}
                Click Element    //div[@name='${item_name}']/div[@id='add_to_cart']
        
        It is also possible to report only if ``Sleep`` exceeds given time limit using ``max_time`` parameter::
        
            robocop -c sleep-keyword-used:max_time:1min .

        """,
    ),
    "10002": Rule(
        RuleParam(
            name="keywords",
            default=None,
            converter=comma_separated_list,
            desc="Comma separated list of not allowed keywords",
        ),
        rule_id="10002",
        name="not-allowed-keyword",
        msg="Keyword '{{ keyword }}' is not allowed",
        severity=RuleSeverity.WARNING,
        added_in_version="5.1.0",
        enabled=False,
        docs="""
        Reports usage of not allowed keywords.
        
        Configure which keywords should be reported by using ``keywords`` parameter.
        Keyword names are normalized to match Robot Framework search behaviour (lower case, removed whitespace and
        underscores). 

        For example::
        
            > robocop -i not-allowed-keyword -c not-allowed-keyword:keywords:click_using_javascript

            *** Keywords ***
            Keyword With Obsolete Implementation
                [Arguments]    ${locator}
                Click Using Javascript    ${locator}  # Robocop will report not allowed keyword

        If keyword call contains possible library name (ie. Library.Keyword Name), Robocop checks if it matches
        the not allowed keywords and if not, it will remove library part and check again.

        """,
    ),
}


class SleepKeywordUsedChecker(VisitorChecker):
    """
    Find and report use of the Sleep keyword in tests and keywords.

    If max_time is configured, it can be used to only report Sleep with time higher than configured value.

    Sleep in Run Keyword variants and with BDD are ignored.
    """

    reports = ("sleep-keyword-used",)

    def visit_KeywordCall(self, node):  # noqa
        if not node.keyword:  # Keyword name can be empty if the syntax is invalid
            return
        # Robot Framework ignores case, underscores and whitespace when searching for keywords
        # It will match sleep, Sleep, BuiltIn.Sleep or S_leep. That's why we need to normalize name first
        normalized_name = normalize_robot_name(node.keyword, remove_prefix="builtin.")
        if normalized_name != "sleep":
            return
        # retrieve sleep time: get first argument-like token from keyword node. Returns None if token does not exist
        time_token = node.get_token(Token.ARGUMENT)
        allowed_time = self.param("sleep-keyword-used", "max_time")
        if allowed_time:
            if not time_token:  # Sleep without time
                return
            try:
                time_from_sleep = timestr_to_secs(time_token.value)
            except ValueError:
                # ignore invalid or not recognized time string
                return
            if allowed_time >= time_from_sleep:  # if Sleep time is less than allowed maximum, we can ignore issue
                return
        # node can be multiline, ie Sleep ...  1 min -> report either just Sleep, or multi-line report
        duration_time = time_token.value if time_token else ""
        name_token = node.get_token(Token.KEYWORD)
        self.report(
            "sleep-keyword-used",
            duration_time=duration_time,
            node=name_token,
            col=name_token.col_offset + 1,
            end_col=name_token.end_col_offset + 1,
        )


class NotAllowedKeyword(VisitorChecker):
    reports = ("not-allowed-keyword",)

    def check_keyword_naming_with_subkeywords(self, node, name_token_type):
        for keyword in iterate_keyword_names(node, name_token_type):
            self.check_keyword_naming(keyword.value, keyword)

    def check_keyword_naming(self, name: str, keyword):
        if not name:
            return
        not_allowed = self.param("not-allowed-keyword", "keywords")
        normalized_name = normalize_robot_name(name)
        if normalized_name not in not_allowed:
            if "." not in normalized_name:
                return
            # handle possible library names (builtin.log)
            normalized_name = normalized_name.split(".")[-1]
            if normalized_name not in not_allowed:
                return
        self.report(
            "not-allowed-keyword",
            keyword=name,
            node=keyword,
            col=keyword.col_offset + 1,
            end_col=keyword.end_col_offset + 1,
        )

    def visit_Setup(self, node):  # noqa
        self.check_keyword_naming_with_subkeywords(node, Token.NAME)

    visit_TestTeardown = visit_SuiteTeardown = visit_Teardown = visit_TestSetup = visit_SuiteSetup = visit_Setup

    def visit_Template(self, node):  # noqa
        # allow / disallow param
        if node.value:
            name_token = node.get_token(Token.NAME)
            self.check_keyword_naming(node.value, name_token)
        self.generic_visit(node)

    visit_TestTemplate = visit_Template

    def visit_KeywordCall(self, node):  # noqa
        self.check_keyword_naming_with_subkeywords(node, Token.KEYWORD)
