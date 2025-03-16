from __future__ import annotations

from robocop.errors import FatalError


class RobocopConfigError(FatalError): ...


class InvalidParameterValueError(RobocopConfigError):
    def __init__(self, formatter, param, value, msg):
        exc_msg = f"{formatter}: Invalid '{param}' parameter value: '{value}'. {msg}"
        super().__init__(exc_msg)


class InvalidParameterError(RobocopConfigError):
    def __init__(self, formatter, similar):
        super().__init__(
            f"{formatter}: Failed to import. Verify if correct name or configuration was provided.{similar}"
        )


class ImportFormatterError(RobocopConfigError):
    pass
