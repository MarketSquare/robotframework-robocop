class RobocopFatalError(ValueError):
    pass


class ConfigGeneralError(RobocopFatalError):
    pass


class InvalidExternalCheckerError(RobocopFatalError):
    def __init__(self, path):
        msg = f'Fatal error: Failed to load external rules from file "{path}". Verify if the file exists'
        super().__init__(msg)


class FileError(RobocopFatalError):
    def __init__(self, source):
        msg = f'File "{source}" does not exist'
        super().__init__(msg)


class ArgumentFileNotFoundError(RobocopFatalError):
    def __init__(self, source):
        msg = f'Argument file "{source}" does not exist'
        super().__init__(msg)


class NestedArgumentFileError(RobocopFatalError):
    def __init__(self, source):
        msg = f'Nested argument file in "{source}"'
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


class RuleParamNotFoundError(RobocopFatalError):
    def __init__(self, rule, param, checker):
        super().__init__(
            f"Rule `{rule.name}` in `{checker.__class__.__name__}` checker does not contain `{param}` param. "
            f"Available params:\n    {rule.available_configurables()}"
        )


class RuleParamFailedInitError(RobocopFatalError):
    def __init__(self, param, value, err):
        desc = f"    Parameter info: {param.desc}" if param.desc else ""
        super().__init__(
            f"Failed to configure param `{param.name}` with value `{value}`. Received error `{err}`.\n"
            f"    Parameter type: {param.converter}\n" + desc
        )


class RuleReportsNotFoundError(RobocopFatalError):
    def __init__(self, rule, checker):
        super().__init__(f"{checker.__class__.__name__} checker `reports` attribute contains unknown rule `{rule}`")
