from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter import sonar_qube
from robocop.linter.fix import Fix, FixApplicability, FixAvailability, TextEdit
from robocop.linter.rules import FixableRule, Rule, RuleParam, RuleSeverity
from robocop.linter.rules.keywords import comma_separated_list

if TYPE_CHECKING:
    from robocop.linter.diagnostics import Diagnostic


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

    """

    name = "unused-keyword"
    project_rule = True
    rule_id = "KW04"
    message = "Keyword '{keyword_name}' is not used"
    severity = RuleSeverity.INFO
    enabled = False
    added_in_version = "5.3.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("10101",)


class KeywordNotFoundRule(Rule):
    """
    Keyword is not defined anywhere.

    Reports keyword calls that do not match any keyword defined in the file, in the imported resource files or in
    the imported libraries. Robot Framework fails such call with the ``No keyword with name 'X' found`` error.

    Example of rule violation:

        *** Settings ***
        Resource    login.resource   # defines Login

        *** Test Cases ***
        Test
            Login    user    password
            Logout                    # Logout is not defined anywhere

    Keywords come from libraries more often than not, so this rule requires the library analysis and is only
    executed together with the ``--analyze-libraries`` option::

        robocop check --select keyword-not-found --analyze-libraries

    To avoid false positives, calls are not reported when the keywords available in the file are not fully known:

    - the keyword name is built from a variable,
    - any import of the file or of the resources it imports could not be resolved,
    - any imported library could not be imported, for example because it is not installed or its arguments could
      not be resolved,
    - the file or any of the imported resources imports libraries or resources dynamically, using the
      ``Import Library`` or ``Import Resource`` keywords.

    Libraries excluded with the ``--ignored-library`` option make all files importing them skipped as well.

    """

    name = "keyword-not-found"
    project_rule = True
    rule_id = "KW05"
    message = "Keyword '{keyword_name}' not found"
    severity = RuleSeverity.ERROR
    enabled = False
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.LOGICAL, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )


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

    """

    name = "ambiguous-keyword-name"
    project_rule = True
    rule_id = "KW06"
    message = "Keyword '{keyword_name}' matches keywords from multiple sources: {sources}"
    severity = RuleSeverity.WARNING
    enabled = False
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.LOGICAL, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )


class MissingKeywordPrefixRule(FixableRule):
    """
    Keyword is called without the name of the resource file or library it comes from.

    Optional rule for projects that require every keyword call to be prefixed with the source of the keyword.
    Such calls are unambiguous and it is immediately clear where the keyword comes from:

        *** Settings ***
        Resource       login.resource
        Library        SeleniumLibrary

        *** Test Cases ***
        Test
            Login    user    password        # will be reported
            Click Element    id:submit       # will be reported

            login.Login    user    password  # explicit, not reported
            SeleniumLibrary.Click Element    id:submit

    The rule is not enabled by default. Select it to use it:

        robocop check --select missing-keyword-prefix

    Libraries imported with the ``AS`` (``WITH NAME``) syntax are expected to be called using the alias.
    Keywords defined in the file with the call are never reported, since there is nothing to prefix them with.

    ``BuiltIn`` keywords are not reported by default. Configure ``ignored_sources`` with a comma separated list of
    resource file, library and alias names to change it:

        robocop check --select missing-keyword-prefix -c missing-keyword-prefix.ignored_sources=BuiltIn,Collections

    To avoid false positives, the call is not reported when:

    - the keyword name is built from a variable,
    - the keyword name already contains a dot, since it may be prefixed already,
    - the keyword is not found in the project, or more than one definition matches the name.

    Keywords coming from libraries are only reported if the library analysis is enabled (it is by default).

    """

    name = "missing-keyword-prefix"
    project_rule = True
    rule_id = "KW07"
    message = "Keyword '{keyword_name}' should be called with the '{prefix}' prefix"
    severity = RuleSeverity.WARNING
    enabled = False
    added_in_version = "9.0.0"
    fix_availability = FixAvailability.ALWAYS
    fix_suggestion = "Add the name of the resource file or library to the keyword call"
    parameters = [
        RuleParam(
            name="ignored_sources",
            default="BuiltIn",
            converter=comma_separated_list,
            show_type="str",
            desc="Comma separated list of the resource files and libraries that do not require the prefix",
        )
    ]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        prefix = str(diag.reported_arguments["prefix"])
        offset = int(diag.reported_arguments["prefix_offset"])  # type: ignore[call-overload]
        column = diag.range.start.character + offset
        edit = TextEdit(
            rule_id=self.rule_id,
            rule_name=self.name,
            start_line=diag.range.start.line,
            start_col=column,
            end_line=diag.range.start.line,
            end_col=column,
            replacement=f"{prefix}.",
        )
        return Fix(edits=[edit], message=f"Add '{prefix}' prefix", applicability=FixApplicability.SAFE)
