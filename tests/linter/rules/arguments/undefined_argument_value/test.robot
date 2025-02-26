*** Test Cases ***
With undefined value
    Log    message=
    Log    message=    level=
    Log    Hello world    level=    html=${True}
    Log    A great log message=
    Log    A great log message =

With escaped equals sign
    Log    A great log message \=
    Log    A great log message\=
    Log    Hello\=world
    Log    mess\=age=foo

With defined values
    Log    Hello = world
    Log    message=Hello world
    Log    message==
    Log    =
    Log    = amazing!
