*** Settings ***
Suite Setup    Not Allowed
Suite Teardown
Test Setup    Not Allowed
Test Teardown    Not Allowed With Args
...    ${arg}


*** Test Cases ***
Test with allowed keywords
    Allowed
    Allowed With Args    ${arg}

Test with not allowed keywords
    Not Allowed
    IF    $condition    Notallowed
    FOR    ${var}    IN RANGE    10
        Not_allowed With Args    ${arg}
        ...    ${arg}
    END
    IF    True
        Log    statement
        Not Allowed
    END

Test with settings
    [Setup]    Run Keywords
    ...    Not Allowed
    ...    AND
    ...    Not Allowed
    [Teardown]    Not Allowed With Args    ${arg}

Test with template
    [Template]    Not Allowed

Test with library
    Not Allowed With Lib  # should be ignored
    Library.Not Allowed With Lib  # should be reported
    Library2.Nested.Not Allowed  # should be reported


*** Keywords ***
Keyword with not allowed
    Not Allowed

# while and stuff?
