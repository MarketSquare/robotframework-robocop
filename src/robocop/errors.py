from __future__ import annotations

from typing import TYPE_CHECKING

import typer
from rich.console import Console
from robot.errors import DataError

if TYPE_CHECKING:
    from robocop.linter.rules import Rule


class FatalError(typer.Exit):
    def __init__(self, msg: str):
        console = Console(stderr=True)
        console.print(f"[red]{self.__class__.__name__}[/red]: {msg}")
        super().__init__(code=2)


class InvalidConfigurationError(FatalError):
    pass


class InvalidParameterValueError(InvalidConfigurationError):
    def __init__(self, formatter, param, value, msg):
        exc_msg = f"{formatter}: Invalid '{param}' parameter value: '{value}'. {msg}"
        super().__init__(exc_msg)


class InvalidParameterError(InvalidConfigurationError):
    def __init__(self, formatter, similar):
        super().__init__(
            f"{formatter}: Failed to import. Verify if correct name or configuration was provided.{similar}"
        )


class ImportFormatterError(InvalidConfigurationError):
    pass


class InvalidConfigurationFormatError(InvalidConfigurationError):
    def __init__(self, name: str):
        super().__init__(f"'{name}': Invalid configuration format. Pass parameters using name.param_name=value syntax.")


class ConfigurationError(FatalError):
    pass


class InvalidExternalCheckerError(FatalError):
    def __init__(self, path):
        msg = f'Fatal error: Failed to load external rules from file "{path}". Verify if the file exists'
        super().__init__(msg)


class RuleParamNotFoundError(FatalError):  # TODO, not used
    def __init__(self, rule, param, checker):
        super().__init__(
            f"Rule `{rule.name}` in `{checker.__class__.__name__}` checker does not contain `{param}` param. "
            f"Available params:\n    {rule.available_configurables()[1]}"
        )


class RuleParamFailedInitError(FatalError):
    def __init__(self, param, value, err):
        desc = f"    Parameter info: {param.desc}" if param.desc else ""
        super().__init__(
            f"Failed to configure param `{param.name}` with value `{value}`. Received error `{err}`.\n"
            f"    Parameter type: {param.converter}\n" + desc
        )


class InvalidReportName(FatalError):
    def __init__(self, report, reports):
        from robocop.linter.utils.misc import RecommendationFinder

        report_names = sorted([*list(reports.keys()), "all"])
        similar = RecommendationFinder().find_similar(report, report_names)
        msg = f"Provided report '{report}' does not exist. {similar}"
        super().__init__(msg)


class RuleDoesNotExist(FatalError):  # not used atm
    def __init__(self, rule: str, rules: dict[str, Rule]):
        from robocop.linter.utils.misc import RecommendationFinder

        similar = RecommendationFinder().find_similar(rule, rules)
        msg = f"Provided rule '{rule}' does not exist. {similar}"
        super().__init__(msg)


class RuleOrReportDoesNotExist(FatalError):  # not used atm
    def __init__(self, rule: str, rules: dict[str, Rule]):
        from robocop.linter.utils.misc import RecommendationFinder

        similar = RecommendationFinder().find_similar(rule, rules)
        msg = f"Provided rule or report '{rule}' does not exist. {similar}"
        super().__init__(msg)


class RobotFrameworkParsingError(Exception):
    def __init__(self):
        msg = (
            "Fatal exception occurred when using Robot Framework parsing module. "
            "Consider updating Robot Framework to recent stable version."
        )
        super().__init__(msg)


def handle_robot_errors(func):
    """
    Handle bugs in Robot Framework.

    If the user uses older version of Robot Framework, it may fail while parsing the
    source code due to bug that is already fixed in the more recent version.
    """

    def wrap_errors(*args, **kwargs):  # noqa: ANN202
        try:
            return func(*args, **kwargs)
        except DataError:
            raise
        except Exception as err:
            raise RobotFrameworkParsingError from err

    return wrap_errors
