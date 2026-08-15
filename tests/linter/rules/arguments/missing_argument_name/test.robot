*** Settings ***
Resource    keywords.resource

*** Test Cases ***
Named Calls
    Login    username=user    password=pass
    With Default    a=1
    With Kwargs    a=1    other=2
    No Args
    Named Only    a=1    strict=yes

Positional Calls
    Login    user    pass
    With Default    1
    With Default    1    2
    With Kwargs    1    other=2

Guarded Calls
    ${name} =    Set Variable    Login
    Run Keyword    ${name}
    Login    @{args}
    Login    &{kwargs}
    Unknown Library Keyword    a    b    c
    Embedded value Keyword
    With Varargs    1    2    3
    Log    anything

Value With Equal Sign
    Login    user=name    pass

Templated Test
    [Template]    Login
    user    pass
