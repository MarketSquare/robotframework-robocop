from enum import Enum
from copy import deepcopy


class MessageSeverity(Enum):
    INFO = "I"
    WARNING = "W"
    ERROR = "E"
    FATAL = "F"


class Message:
    def __init__(self, msg_id, body):
        self.msg_id = msg_id
        self.body = body
        self.name = ''
        self.desc = ''
        self.source = None
        self.line = -1
        self.col = -1
        self.severity = MessageSeverity.INFO
        self.configurable = []
        self.parse_body()

    def get_fullname(self):
        return f"{self.severity.value}{self.msg_id} ({self.name})"

    def get_configurable(self, param):
        for configurable in self.configurable:
            if configurable[0] == param:
                return configurable
        else:
            return None

    def parse_body(self):
        try:
            self.name, self.desc, self.severity, *self.configurable = self.body
        except ValueError:
            pass

    def prepare_message(self, *args, source, node, lineno, col):
        message = deepcopy(self)
        message.desc %= args
        message.source = source
        if lineno is None and node is not None:
            lineno = node.lineno
        message.line = lineno
        if col is None:
            col = 0
        message.col = col
        return message