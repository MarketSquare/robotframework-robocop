from robocop import checkers


if __name__ == "__main__":
    severity = "    Severity: (:class:`.MessageSeverity`)"
    checker_docs = {}
    for checker in checkers.get_docs():
        checker_doc = 'Reports: \n'
        for msg, msg_def in checker.msgs.items():
            checker_doc += f" * [{msg_def[2].value}{msg}] {msg_def[0]}: {msg_def[1]}\n\n"
            checker_doc += "    Configurable parameters:\n"
            checker_doc += severity
            if len(msg_def) > 3:
                checker_doc += f"    {msg_def[3][0]} ({msg_def[3][2]})"
            checker_docs[checker.__name__] = checker_doc
            print(checker.__module__)
            print(checker.__bases__)
