import sys


class RobocopFatalError(ValueError):
    pass


class ConfigGeneralError(RobocopFatalError):
    def __init__(self, msg):
        super().__init__(msg)


class DuplicatedMessageError(RobocopFatalError):
    def __init__(self, msg_type, msg, checker, checker_prev):
        msg = f"Fatal error: Message {msg_type} '{msg}' defined in {checker.__class__.__name__} " \
              f"was already defined in {checker_prev.__class__.__name__}"
        super().__init__(msg)


class InvalidMessageSeverityError(RobocopFatalError):
    def __init__(self, msg, severity_val):
        msg = f"Fatal error: Tried to configure message {msg} with invalid severity: {severity_val}"
        super().__init__(msg)


class InvalidMessageBodyError(RobocopFatalError):
    def __init__(self, msg_id, msg_body):
        msg = f"Fatal error: Message '{msg_id}' has invalid body:\n{msg_body}"
        super().__init__(msg)


class InvalidMessageConfigurableError(RobocopFatalError):
    def __init__(self, msg_id, msg_body):
        msg = f"Fatal error: Message '{msg_id}' has invalid configurable:\n{msg_body}"
        super().__init__(msg)


class InvalidMessageUsageError(RobocopFatalError):
    def __init__(self, msg_id, type_error):
        msg = f"Fatal error: Message '{msg_id}' failed to prepare message description with error:{type_error}"
        super().__init__(msg)


class FileError:
    def __init__(self, source):
        print(f"File {source} does not exist", file=sys.stderr)
        sys.exit(1)
