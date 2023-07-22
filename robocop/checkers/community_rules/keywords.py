from robot.api import Token
from robot.utils.robottime import timestr_to_secs

from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleParam, RuleSeverity
from robocop.utils.misc import normalize_robot_name

RULE_CATEGORY_ID = "00"

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
    )
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
