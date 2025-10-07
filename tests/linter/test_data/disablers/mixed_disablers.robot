*** Test Cases ***
Mixed disablers
    Test  # robocop: off=rule robocop: fmt: off=Formatter
    Test  # robocop: off robocop: fmt: off=Formatter
    Test  # robocop: off robocop: fmt: off
    Test  # robocop: fmt: off =Formatter robocop: off=rule
    Test  # robocop: fmt: off= Formatter robocop: off
    Test  # robocop: fmt: off robocop: off

Multiple disablers
    Test  # robocop: fmt: off=Formatter, Formatter2 robocop: off
    Test  # robocop: fmt: off=Formatter,Formatter2 robocop: off
    Test  # robocop: fmt: off = Formatter robocop: off robocop: fmt: off=Formatter2
    Test  # robocop: off=rule some text robocop: off=rule2
    Test  # robocop: off=rule1,rule2 robocop: off
    Test  # robocop: off=rule1,rule2
    Test  # robocop: off=rule1, rule2
    Test  # robocop: off=rule1
