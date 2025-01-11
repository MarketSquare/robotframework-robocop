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
    Log    message=Hello=
    Log    message==
    Log    =
    Log    = amazing!

Additional edge cases
    # https://github.com/MarketSquare/robotframework-robocop/issues/1160
    Push Buttons    C${expression}=
    Get Text    xpath=(//h4)[5]    *=    min
    Get Text    xpath=(//h4)[5]    ==    min
