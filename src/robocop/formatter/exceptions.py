from __future__ import annotations

import sys


class RobocopConfigError(Exception):
    def __init__(self, err):
        print(f"Error: {err}")
        sys.exit(1)


class InvalidParameterValueError(RobocopConfigError):
    def __init__(self, formatter, param, value, msg):
        exc_msg = f"{formatter}: Invalid '{param}' parameter value: '{value}'. {msg}"
        super().__init__(exc_msg)


class InvalidParameterError(RobocopConfigError):
    def __init__(self, formatter, similar):
        super().__init__(
            f"{formatter}: Failed to import. Verify if correct name or configuration was provided.{similar}"
        )


class InvalidParameterFormatError(RobocopConfigError):
    def __init__(self, formatter):
        super().__init__(
            f"{formatter}: Invalid parameter format. Pass parameters using MyFormatter.param_name=value syntax."
        )


class ImportFormatterError(RobocopConfigError):
    pass
