from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from robocop.linter.rules import Rule

import robot.errors


class RobocopFatalError(ValueError):
    pass


class ConfigGeneralError(RobocopFatalError):
    pass


class InvalidExternalCheckerError(RobocopFatalError):
    def __init__(self, path):
        msg = f'Fatal error: Failed to load external rules from file "{path}". Verify if the file exists'
        super().__init__(msg)


class InvalidArgumentError(RobocopFatalError):
    def __init__(self, msg):
        super().__init__(f"Invalid configuration for Robocop:\n{msg}")


class RuleNotFoundError(RobocopFatalError):
    def __init__(self, rule, checker):
        super().__init__(
            f"{checker.__class__.__name__} checker does not contain rule `{rule}`. "
            f"Available rules: {', '.join(checker.rules.keys())}"
        )


class RuleParamNotFoundError(RobocopFatalError):  # TODO
    def __init__(self, rule, param, checker):
        super().__init__(
            f"Rule `{rule.name}` in `{checker.__class__.__name__}` checker does not contain `{param}` param. "
            f"Available params:\n    {rule.available_configurables()[1]}"
        )


class RuleParamFailedInitError(RobocopFatalError):  # TODO
    def __init__(self, param, value, err):
        desc = f"    Parameter info: {param.desc}" if param.desc else ""
        super().__init__(
            f"Failed to configure param `{param.name}` with value `{value}`. Received error `{err}`.\n"
            f"    Parameter type: {param.converter}\n" + desc
        )


class InvalidReportName(ConfigGeneralError):
    def __init__(self, report, reports):
        from robocop.linter.utils import RecommendationFinder

        report_names = sorted([*list(reports.keys()), "all"])
        similar = RecommendationFinder().find_similar(report, report_names)
        msg = f"Provided report '{report}' does not exist. {similar}"
        super().__init__(msg)


class RuleDoesNotExist(ConfigGeneralError):
    def __init__(self, rule: str, rules: dict[str, "Rule"]):
        from robocop.linter.utils import RecommendationFinder

        similar = RecommendationFinder().find_similar(rule, rules)
        msg = f"Provided rule '{rule}' does not exist. {similar}"
        super().__init__(msg)


class RuleOrReportDoesNotExist(ConfigGeneralError):
    def __init__(self, rule: str, rules: dict[str, "Rule"]):
        from robocop.linter.utils import RecommendationFinder

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
        except robot.errors.DataError:
            raise
        except Exception as err:
            raise RobotFrameworkParsingError from err

    return wrap_errors
