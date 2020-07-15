from robocop import checkers
from pathlib import Path
from importlib import import_module


if __name__ == "__main__":
    for checker in checkers.get_docs():
        print(checker.__name__)
        print(checker.__doc__)
        print('    Available messages: ')
        for msg, msg_def in checker.msgs.items():
            print(f"    [{msg_def[2].value}{msg}] {msg_def[0]}: {msg_def[1]}")
            print('       Configurable parameters: ')
            print('         severity (MessageSeverityEnum)')
            if len(msg_def) > 3:
                print(f"         {msg_def[3][0]} ({msg_def[3][2]})")
