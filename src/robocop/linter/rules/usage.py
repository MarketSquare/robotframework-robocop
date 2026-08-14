from __future__ import annotations

from robocop.linter import sonar_qube
from robocop.linter.rules import Rule, RuleSeverity


class UnusedKeywordRule(Rule):
    """
    Keyword is not used.

    Reports keywords that are defined in the project but never called.

    Example:

        *** Test Cases ***
        Test that only non used keywords are reported
            Used Keyword

        *** Keywords ***
        Used Keyword
            Log    used

        Not Used Keyword  # this keyword will be reported as not used
            [Arguments]    ${arg}
            Should Be True    ${arg}>50

    A keyword is considered used when it is called anywhere in the project, including test setups, teardowns and
    templates, and keywords nested in ``Run Keyword`` variants. Keywords marked with the ``robot:private`` tag can
    only be used in the file they are defined in, so only calls from that file are taken into account.

    To avoid false positives, a keyword is not reported when it may be called with a name built from a variable.
    For example, a call to ``Login ${type}`` marks both ``Login Admin`` and ``Login User`` as used.

    Keywords are only searched for in the files scanned by Robocop. If the project is a shared library of keywords
    used by other projects, all of its keywords are reported as not used.

    This rule is a project level rule: it requires parsing the whole project. Selecting it makes ``robocop check``
    analyze the project.

    """

    name = "unused-keyword"
    rule_id = "KW04"
    message = "Keyword '{keyword_name}' is not used"
    severity = RuleSeverity.INFO
    enabled = False
    added_in_version = "5.3.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("10101",)


class AmbiguousKeywordNameRule(Rule):
    """
    Keyword name matches more than one keyword.

    Reports keyword calls that match keywords defined in more than one place. Robot Framework fails such call
    with the ``Multiple keywords with name 'X' found`` error, unless the call uses the full name of the keyword.

    Example of rule violation:

        *** Settings ***
        Resource    login.resource      # defines Login
        Resource    admin.resource      # defines Login as well

        *** Test Cases ***
        Test
            Login    user    password   # it is not known which keyword should be used

    Robot Framework resolves conflicts using the following order, which the rule follows as well:

    - a keyword defined in the file containing the call is always used,
    - keywords from resource files are used before keywords from libraries,
    - a keyword from a custom library is used before a keyword from a standard library.

    Calls using the full name of the keyword (``login.Login``) are not reported, since the prefix already
    selects the keyword. Calls with a name built from a variable are not reported either.

    Keywords defined twice in the same file are reported by the ``duplicated-keyword-name`` rule instead.

    This rule is a project level rule: it requires parsing the whole project. Selecting it makes ``robocop check``
    analyze the project.

    """

    name = "ambiguous-keyword-name"
    rule_id = "KW06"
    message = "Keyword '{keyword_name}' matches keywords from multiple sources: {sources}"
    severity = RuleSeverity.WARNING
    enabled = False
    added_in_version = "8.9.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.LOGICAL, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
