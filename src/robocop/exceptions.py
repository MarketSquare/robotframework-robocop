from __future__ import annotations

from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

import typer
from rich.console import Console
from robot.errors import DataError

if TYPE_CHECKING:
    from collections.abc import Callable

    from robocop.linter.reports import Report
    from robocop.linter.rules import Rule, RuleParam

_P = ParamSpec("_P")
_R = TypeVar("_R")


class FatalError(typer.Exit):
    def __init__(self, msg: str):
        console = Console(stderr=True)
        console.print(f"[red]{self.__class__.__name__}[/red]: {msg}")
        super().__init__(code=2)


class InvalidConfigurationError(FatalError):
    pass


class InvalidParameterValueError(InvalidConfigurationError):
    def __init__(self, formatter: str, param: str, value: object, msg: str) -> None:
        exc_msg = f"{formatter}: Invalid '{param}' parameter value: '{value}'. {msg}"
        super().__init__(exc_msg)


class InvalidParameterError(InvalidConfigurationError):
    def __init__(self, formatter: str, similar: str) -> None:
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
    def __init__(self, path: str) -> None:
        msg = f'Fatal error: Failed to load external rules from file "{path}". Verify if the file exists'
        super().__init__(msg)


class RuleParamNotFoundError(FatalError):  # TODO, not used
    def __init__(self, rule: Rule, param: str, checker: object) -> None:
        super().__init__(
            f"Rule `{rule.name}` in `{checker.__class__.__name__}` checker does not contain `{param}` param. "
            f"Available params:\n    {rule.available_configurables()[1]}"
        )


class RuleParamFailedInitError(FatalError):
    def __init__(self, param: RuleParam, value: Any, err: Exception) -> None:
        desc = f"    Parameter info: {param.desc}" if param.desc else ""
        super().__init__(
            f"Failed to configure param `{param.name}` with value `{value}`. Received error `{err}`.\n"
            f"    Parameter type: {param.converter}\n" + desc
        )


class InvalidReportName(FatalError):
    def __init__(self, report: str, reports: dict[str, Report]) -> None:
        from robocop.linter.utils.misc import RecommendationFinder  # noqa: PLC0415

        report_names = sorted([*list(reports.keys()), "all"])
        similar = RecommendationFinder().find_similar(report, report_names)
        msg = f"Provided report '{report}' does not exist. {similar}"
        super().__init__(msg)


class RuleDoesNotExist(FatalError):  # not used atm
    def __init__(self, rule: str, rules: dict[str, Rule]):
        from typing import cast  # noqa: PLC0415

        from robocop.linter.utils.misc import RecommendationFinder  # noqa: PLC0415

        rules_dict: dict[str, object] = cast("dict[str, object]", rules)
        similar = RecommendationFinder().find_similar(rule, rules_dict)
        msg = f"Provided rule '{rule}' does not exist. {similar}"
        super().__init__(msg)


class RobotFrameworkParsingError(Exception):
    def __init__(self) -> None:
        msg = (
            "Fatal exception occurred when using Robot Framework parsing module. "
            "Consider updating Robot Framework to recent stable version."
        )
        super().__init__(msg)


class CircularExtendsReferenceError(FatalError):
    def __init__(self, config_path: str):
        super().__init__(f"Circular reference found in 'extends' parameter in the configuration file: {config_path}")


def handle_robot_errors(func: Callable[_P, _R]) -> Callable[_P, _R]:
    """
    Handle bugs in Robot Framework.

    If the user uses an older version of Robot Framework, it may fail while parsing the
    source code due to a bug that is already fixed in the more recent version.
    """

    def wrap_errors(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        try:
            return func(*args, **kwargs)
        except DataError:
            raise
        except Exception as err:
            raise RobotFrameworkParsingError from err

    return wrap_errors
