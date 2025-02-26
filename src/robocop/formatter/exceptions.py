from __future__ import annotations

import sys

from click import NoSuchOption

from robocop.formatter.utils import misc


class RobotidyConfigError(Exception):
    def __init__(self, err):
        print(f"Error: {err}")
        sys.exit(1)


class InvalidParameterValueError(RobotidyConfigError):
    def __init__(self, formatter, param, value, msg):
        exc_msg = f"{formatter}: Invalid '{param}' parameter value: '{value}'. {msg}"
        super().__init__(exc_msg)


class InvalidParameterError(RobotidyConfigError):
    def __init__(self, formatter, similar):
        super().__init__(
            f"{formatter}: Failed to import. Verify if correct name or configuration was provided.{similar}"
        )


class InvalidParameterFormatError(RobotidyConfigError):
    def __init__(self, formatter):
        super().__init__(
            f"{formatter}: Invalid parameter format. Pass parameters using MyFormatter.param_name=value syntax."
        )


class ImportFormatterError(RobotidyConfigError):
    pass


class MissingOptionalRichDependencyError(RobotidyConfigError):
    def __init__(self):
        msg = "It looks like you have rich module uninstalled. Install it to be able to use robotidy in the cli mode."
        super().__init__(msg)


class MissingOptionalTomliWDependencyError(RobotidyConfigError):
    def __init__(self):
        super().__init__(
            "Missing optional dependency: tomli_w. Install robotidy with extra `generate_config` "
            "profile:\n\npip install robotframework-tidy[generate_config]"
        )


class NoSuchOptionError(NoSuchOption):
    def __init__(self, option_name: str, allowed_options: list[str]):
        rec_finder = misc.RecommendationFinder()
        similar = rec_finder.find(option_name, allowed_options)
        super().__init__(option_name, possibilities=similar)
