class RobocopFatalError(ValueError):
    pass


class ConfigGeneralError(RobocopFatalError):
    pass


class DuplicatedRuleError(RobocopFatalError):
    def __init__(self, rule_type, rule, checker, checker_prev):
        msg = f"Fatal error: Message {rule_type} '{rule}' defined in {checker.__class__.__name__} " \
              f"was already defined in {checker_prev.__class__.__name__}"
        super().__init__(msg)


class InvalidRuleSeverityError(RobocopFatalError):
    def __init__(self, rule, severity_val):
        msg = f"Fatal error: Tried to configure message {rule} with invalid severity: {severity_val}"
        super().__init__(msg)


class InvalidRuleBodyError(RobocopFatalError):
    def __init__(self, rule_id, rule_body):
        msg = f"Fatal error: Rule '{rule_id}' has invalid body:\n{rule_body}"
        super().__init__(msg)


class InvalidRuleConfigurableError(RobocopFatalError):
    def __init__(self, rule_id, rule_body):
        msg = f"Fatal error: Rule '{rule_id}' has invalid configurable:\n{rule_body}"
        super().__init__(msg)


class InvalidRuleUsageError(RobocopFatalError):
    def __init__(self, rule_id, type_error):
        msg = f"Fatal error: Rule '{rule_id}' failed to prepare message description with error: {type_error}"
        super().__init__(msg)


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
