import sys


class RobocopFatalError(Exception):
    def __init__(self):
        sys.exit(1)


class DuplicatedMessageError(RobocopFatalError):
    def __init__(self, msg_type, msg, checker, checker_prev):
        print(f"Fatal error: Message {msg_type} '{msg}' defined in {checker.__class__.__name__} "
              f"was already defined in {checker_prev.__class__.__name__}", file=sys.stderr)
        super().__init__()


class InvalidMessageSeverityError(RobocopFatalError):
    def __init__(self, msg, severity_val):
        print(f"Fatal error: Tried to configure message {msg} with invalid severity: {severity_val}", file=sys.stderr)
        super().__init__()


class InvalidMessageBodyError(RobocopFatalError):
    def __init__(self, msg_id, msg_body):
        print(f"Fatal error: Message '{msg_id}' has invalid body:\n{msg_body}", file=sys.stderr)
        super().__init__()


class InvalidMessageConfigurableError(RobocopFatalError):
    def __init__(self, msg_id, msg_body):
        print(f"Fatal error: Message '{msg_id}' has invalid configurable:\n{msg_body}", file=sys.stderr)
        super().__init__()


class InvalidMessageUsageError(RobocopFatalError):
    def __init__(self, msg_id, type_error):
        print(f"Fatal error: Message '{msg_id}' failed to prepare message description with error:{type_error}",
              file=sys.stderr)
        super().__init__()
