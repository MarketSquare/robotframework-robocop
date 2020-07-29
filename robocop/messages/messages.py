"""
Every issue is reported as ``robocop.messages.Message`` object. It can be later printed or used by
post-run reports.

Format output message
---------------------

Output message can be defined with ``-f`` / ``--format`` argument. Default value::

    {source}:{line}:{col} [{severity}] {msg_id} {desc}

Available formats:
  * source: path to file where is the issue
  * line: line number
  * col: column number
  * severity: severity of the message. Value of enum ``robocop.messages.MessageSeverity``
  * msg_id: id of message (ie. 0501)
  * msg_name: name of message (ie. line-too-long)
  * desc: description of message
"""
from enum import Enum
from copy import deepcopy
import robocop.exceptions


class MessageSeverity(Enum):
    """
    Rule message severity.
    It can be configured with ``-c/--configure id_or_msg_name:severity:value``
    Where value can be first letter of severity value or whole name, case insensitive.
    For example ::

        -c line-too-long:severity:e

    Will change line-too-long message severity to error.
    """
    INFO = "I"
    WARNING = "W"
    ERROR = "E"
    FATAL = "F"


class Message:
    def __init__(self, msg_id, body):
        self.msg_id = msg_id
        self.name = ''
        self.desc = ''
        self.source = None
        self.severity = MessageSeverity.INFO
        self.configurable = []
        self.parse_body(body)

    def change_severity(self, value):
        severity = {
            'error': 'E',
            'e': 'E',
            'warning': 'W',
            'w': 'W',
            'info': 'I',
            'i': 'I',
            'fatal': 'F',
            'f': 'F'
        }.get(str(value).lower(), None)
        if severity is None:
            raise robocop.exceptions.InvalidMessageSeverityError(self.name, value)
        self.severity = MessageSeverity(severity)

    def get_fullname(self):
        return f"{self.severity.value}{self.msg_id} ({self.name})"

    def get_configurable(self, param):
        for configurable in self.configurable:
            if configurable[0] == param:
                return configurable
        return None

    def parse_body(self, body):
        if isinstance(body, tuple) and len(body) >= 3:
            self.name, self.desc, self.severity, *self.configurable = body
        else:
            raise robocop.exceptions.InvalidMessageBodyError(self.msg_id, body)
        for configurable in self.configurable:
            if not isinstance(configurable, tuple) or len(configurable) != 3:
                raise robocop.exceptions.InvalidMessageConfigurableError(self.msg_id, body)

    def prepare_message(self, *args, source, node, lineno, col):
        message = deepcopy(self)
        try:
            message.desc %= args
        except TypeError as err:
            raise robocop.exceptions.InvalidMessageUsageError(self.msg_id, err)
        message.source = source
        if lineno is None and node is not None:
            lineno = node.lineno
        message.line = lineno
        if col is None:
            col = 0
        message.col = col
        return message
