from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from robot.api import Token

from robocop.linter import sonar_qube
from robocop.linter.fix import Fix, FixApplicability, FixAvailability, TextEdit
from robocop.linter.rules import FixableRule, Rule, RuleParam, RuleSeverity
from robocop.linter.utils.misc import normalize_robot_var_name, split_argument_default_value, str2bool
from robocop.version_handling import TYPE_SUPPORTED

if TYPE_CHECKING:
    from robot.parsing.model.statements import Arguments, KeywordCall

    from robocop.linter.diagnostics import Diagnostic


class UnusedArgumentRule(Rule):
    """
    Keyword argument was defined but not used:

        *** Keywords ***
        Keyword
            [Arguments]    ${used}    ${not_used}  # will report ${not_used}
            Log    ${used}
            IF    $used
                Log    Escaped syntax is supported.
            END

        Keyword with ${embedded} and ${not_used}  # will report ${not_used}
            Log    ${embedded}

    """

    name = "unused-argument"
    rule_id = "ARG01"
    message = "Keyword argument '{name}' is not used"
    severity = RuleSeverity.WARNING
    added_in_version = "3.2.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0919",)


class ArgumentOverwrittenBeforeUsageRule(Rule):
    """

    Keyword argument was overwritten before it is used:

        *** Keywords ***
        Overwritten Argument
            [Arguments]    ${overwritten}  # we do not use ${overwritten} value at all
            ${overwritten}    Set Variable    value  # we only overwrite it

    """

    name = "argument-overwritten-before-usage"
    rule_id = "ARG02"
    message = "Keyword argument '{name}' is overwritten before usage"
    severity = RuleSeverity.WARNING
    added_in_version = "3.2.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0921",)


class UndefinedArgumentDefaultRule(FixableRule):
    """
    Keyword arguments can define a default value. Every time you call the keyword, you can
    optionally overwrite this default.

    When you use an argument default, you should be as clear as possible. This improves the
    readability of your code. The syntax ``${argument}=`` is unclear unless you happen to know
    that it is technically equivalent to ``${argument}=${EMPTY}``. To prevent people from
    misreading your keyword arguments, explicitly state that the value is empty using the
    built-in ``${EMPTY}`` variable.

    Example of a rule violation:

        *** Keywords ***
        My Amazing Keyword
            [Arguments]    ${argument_name}=

    The fix adds the explicit ``${EMPTY}`` default value.

    """

    name = "undefined-argument-default"
    rule_id = "ARG03"
    message = "Undefined argument default, use {arg_name}=${{EMPTY}} instead"
    severity = RuleSeverity.WARNING
    added_in_version = "5.7.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0932",)
    fix_availability = FixAvailability.ALWAYS

    def check(self, node: Arguments) -> None:
        if not self.enabled:
            return
        for token in node.get_tokens(Token.ARGUMENT):
            arg = token.value
            arg_name, default_val = split_argument_default_value(arg)
            if arg_name == arg:  # has no default
                continue
            if default_val == "":
                self.report(
                    node=token,
                    lineno=token.lineno,
                    col=token.col_offset + 1,
                    end_col=token.col_offset + len(token.value) + 1,
                    arg_name=arg_name,
                )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        """Add the explicit ``${EMPTY}`` default value after the ``=`` sign."""
        column = diag.range.end.character
        edit = TextEdit(
            rule_id=self.rule_id,
            rule_name=self.name,
            start_line=diag.range.start.line,
            start_col=column,
            end_line=diag.range.start.line,
            end_col=column,
            replacement="${EMPTY}",
        )
        arg_name = diag.reported_arguments["arg_name"]
        return Fix(
            edits=[edit],
            message=f"Add the explicit ${{EMPTY}} default value to the '{arg_name}' argument",
            applicability=FixApplicability.SAFE,
        )


class UndefinedArgumentValueRule(Rule):
    r"""
    When calling a keyword, it can accept named arguments.

    When you call a keyword, you should be as clear as possible. This improves the
    readability of your code. The syntax ``argument=`` is unclear unless you happen to know
    that it is technically equivalent to ``argument=${EMPTY}``. To prevent people from
    misreading your keyword arguments, explicitly state that the value is empty using the
    built-in ``${EMPTY}`` variable.

    If this rule falsely flags your argument, escape the ``=`` character in your argument
    value by like so: ``\=``.

    Example of a rule violation:

        *** Test Cases ***
        Test case
            My Amazing Keyword    argument_name=

    """

    name = "undefined-argument-value"
    rule_id = "ARG04"
    message = "Undefined argument value, use {arg_name}=${{EMPTY}} instead"
    severity = RuleSeverity.WARNING
    added_in_version = "5.7.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0933",)

    # used by AssertionEngine library
    assertion_operators: ClassVar[set[str]] = {"==", "!=", "<", ">", "<=", ">=", "*=", "^=", "$=", "$"}

    def check(self, node: KeywordCall) -> None:
        if not self.enabled:
            return
        for token in node.get_tokens(Token.ARGUMENT):
            arg = token.value
            if arg in self.assertion_operators:
                continue
            if "=" not in arg or arg.startswith("="):  # is a positional arg
                continue
            arg_name, default_val = arg.split("=", maxsplit=1)
            if arg_name.endswith("\\"):  # `=` is escaped
                continue
            if default_val != "":  # has a value
                continue
            # Falsly triggers if a positional argument ends with `=`
            # The language server has the same behavior
            self.report(
                node=token,
                lineno=token.lineno,
                col=token.col_offset + 1,
                end_col=token.col_offset + len(token.value) + 1,
                arg_name=arg_name,
            )


class InvalidArgumentsRule(Rule):
    """
    Argument names should follow variable naming syntax: start with identifier (``$``, ``@`` or ``&``) and enclosed
    in curly brackets (``{}``).

    Valid names:

        *** Keywords ***
        Keyword
            [Arguments]    ${var}    @{args}    &{config}    ${var}=default

    Invalid names:

        *** Keywords ***
        Keyword
            [Arguments]    {var}    @args}    var=default

    """

    name = "invalid-argument"
    rule_id = "ARG05"
    message = "{error_msg}"
    severity = RuleSeverity.ERROR
    version = ">=4.0"
    added_in_version = "1.11.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0407",)


class DuplicatedArgumentRule(Rule):
    """
    Argument name is already used.

    Variable names in Robot Framework are case-insensitive and ignores spaces and underscores. Following arguments
    are duplicates:

        *** Keywords ***
        Keyword
            [Arguments]    ${var}  ${VAR}  ${v_ar}  ${v ar}
            Other Keyword

    """

    name = "duplicated-argument-name"
    rule_id = "ARG06"
    message = "Argument name '{argument_name}' is already used"
    severity = RuleSeverity.WARNING
    added_in_version = "1.11.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0811",)

    def check(self, node: Arguments) -> None:
        if not self.enabled:
            return
        args: set[str] = set()
        for arg in node.get_tokens(Token.ARGUMENT):
            orig, *_ = arg.value.split("=", maxsplit=1)
            name = normalize_robot_var_name(orig, strip_type=TYPE_SUPPORTED)
            if name in args:  # TODO could be handled with other variables rules
                self.report(
                    argument_name=orig,
                    node=node,
                    lineno=arg.lineno,
                    col=arg.col_offset + 1,
                    end_col=arg.col_offset + len(orig) + 1,
                )
            else:
                args.add(name)


class ArgumentsPerLineRule(Rule):
    """
    Too many arguments per continuation line.

    If the keyword's ``[Arguments]`` are split into multiple lines, it is recommended to put only one argument
    per every line.

    Incorrect code example:

        *** Keywords ***
        Keyword With Multiple Arguments
        [Arguments]    ${first_arg}
        ...    ${second_arg}    ${third_arg}=default

    Correct code:

        *** Keywords ***
        Keyword With Multiple Arguments
        [Arguments]    ${first_arg}
        ...    ${second_arg}
        ...    ${third_arg}=default

    """

    name = "arguments-per-line"
    rule_id = "ARG07"
    message = "There is too many arguments per continuation line ({arguments_count} / {max_arguments_count})"
    severity = RuleSeverity.INFO
    parameters = [
        RuleParam(
            name="max_args",
            default=1,
            converter=int,
            desc="maximum number of arguments allowed in the continuation line",
        ),
    ]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0532",)
    # TODO flag to allow for [Arguments] multiple args ine one line, just not in other ...

    def check(self, node: Arguments) -> None:
        if not self.enabled:
            return
        if not node.get_token(Token.CONTINUATION):  # only one line, ignoring
            return
        max_args = self.max_args
        for line in node.lines:
            args_count = sum(1 for token in line if token.type == Token.ARGUMENT)
            if args_count <= max_args:
                continue
            data_token = self.first_non_sep(line)
            if data_token:
                self.report(
                    node=data_token,
                    col=data_token.col_offset + 1,
                    end_col=line[-1].end_col_offset,
                    arguments_count=args_count,
                    max_arguments_count=max_args,
                )

    @staticmethod
    def first_non_sep(line: list[Token]) -> Token | None:
        for token in line:
            if token.type != Token.SEPARATOR:
                return token
        return None


class InvalidArgumentCountRule(Rule):
    """
    Keyword is called with a wrong number of arguments.

    Compares the number of arguments used in the keyword call with the ``[Arguments]`` setting of the keyword
    definition. Such call fails during the execution.

    Example of rule violation:

        *** Test Cases ***
        Test
            Login    user                  # too few arguments
            Login    user    pass    extra # too many arguments

        *** Keywords ***
        Login
            [Arguments]    ${username}    ${password}
            Log    ${username}

    Keywords defined in the project are checked using the ``[Arguments]`` setting. Keywords coming from libraries
    are checked as well, but only if the library analysis is enabled (it is by default). Robocop imports the
    libraries to find out what arguments they accept, which means that the library code is executed. Use the
    ``--no-analyze-libraries`` option to disable it, or ``--ignored-library`` to skip selected libraries.

    To avoid false positives, the call is not reported when:

    - the keyword name is built from a variable,
    - the keyword is not found in the project, or more than one definition matches the name,
    - the keyword uses embedded arguments,
    - the call expands a list (``@{args}``) or dictionary (``&{kwargs}``) variable,
    - the keyword is used as a test template.

    """

    name = "invalid-argument-count"
    project_rule = True
    rule_id = "ARG08"
    message = "Keyword '{keyword_name}' expects {expected} but {provided} provided{missing}"
    severity = RuleSeverity.ERROR
    enabled = False
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.LOGICAL, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )


class MissingArgumentNameRule(FixableRule):
    """
    Keyword is called with a positional argument instead of a named one.

    Optional rule for projects that require every keyword to be called with named arguments. Positional arguments
    are easy to mix up, especially with keywords that accept a lot of them:

        *** Keywords ***
        Create User
            [Arguments]    ${name}    ${surname}    ${age}    ${city}
            Log Many    ${name}    ${surname}    ${age}    ${city}

        *** Test Cases ***
        Test
            Create User    Bob    Smith    30    Berlin  # will report 4 issues

    With this rule enabled, the call should be written as:

        *** Test Cases ***
        Test
            Create User    name=Bob    surname=Smith    age=30    city=Berlin

    The rule is not enabled by default. Select it to use it:

        robocop check --select missing-argument-name

    Argument names are taken from the keyword definition, so the whole project needs to be analyzed. Keywords
    coming from the libraries are ignored by default, since it is not always possible to call them with named
    arguments. Configure ``ignore_library_keywords`` to check them as well:

        robocop check --select missing-argument-name --configure missing-argument-name.ignore_library_keywords=False

    Calls with only a few arguments are often clear enough. Use ``min_arguments`` to only report calls that use
    at least given number of positional arguments:

        robocop check --select missing-argument-name --configure missing-argument-name.min_arguments=3

    To avoid false positives, the argument is not reported when:

    - the keyword name is built from a variable,
    - the keyword is not found in the project, or more than one definition matches the name,
    - the keyword uses embedded arguments,
    - the call expands a list (``@{args}``) or dictionary (``&{kwargs}``) variable,
    - the keyword is used as a test template,
    - the argument is passed to ``*varargs``, or the keyword does not accept it as a named argument.

    """

    name = "missing-argument-name"
    project_rule = True
    rule_id = "ARG09"
    message = "Argument '{argument_name}' of the keyword '{keyword_name}' should be passed as a named argument"
    severity = RuleSeverity.WARNING
    enabled = False
    added_in_version = "9.0.0"
    fix_availability = FixAvailability.ALWAYS
    fix_suggestion = "Add the argument name, for example 'name=Bob' instead of 'Bob'"
    parameters = [
        RuleParam(
            name="ignore_library_keywords",
            default=True,
            converter=str2bool,
            show_type="bool",
            desc="Do not report calls of the keywords imported from the libraries",
        ),
        RuleParam(
            name="min_arguments",
            default=1,
            converter=int,
            desc="Minimal number of the positional arguments in the call required to report it",
        ),
    ]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        argument_name = diag.reported_arguments["argument_name"]
        edit = TextEdit(
            rule_id=self.rule_id,
            rule_name=self.name,
            start_line=diag.range.start.line,
            start_col=diag.range.start.character,
            end_line=diag.range.start.line,
            end_col=diag.range.start.character,
            replacement=f"{argument_name}=",
        )
        return Fix(edits=[edit], message=f"Add '{argument_name}' argument name", applicability=FixApplicability.SAFE)
