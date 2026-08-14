*** Settings ***
Resource    keywords.resource

*** Test Cases ***
Valid Calls
    Login    user    pass
    Login    username=user    password=pass
    Login    user    password=pass
    With Default    1
    With Default    1    2
    With Varargs    1    2    3    4
    With Kwargs    1    other=2
    No Args
    Embedded value Keyword
    Named Only    1    strict=yes
    Log    anything    at    all

Invalid Calls
    Login    user
    Login    user    pass    extra
    With Default
    No Args    unexpected
    Named Only    1

Guarded Calls
    ${name} =    Set Variable    Login
    Run Keyword    ${name}
    Login    @{args}
    Login    &{kwargs}
    Unknown Library Keyword    a    b    c

Nested Calls
    Run Keyword If    True    Login    user
    Run Keywords    No Args    AND    Login    user    pass

Templated Test
    [Template]    Login
    user    pass