*** Settings ***
Resource    keywords.resource
Resource    keywords_alt.resource

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

Mismatched Use In Alt Resource Same Names
    # correct use
    keywords.Args Alt    1
    keywords.No Args Alt
    keywords_alt.Args Alt
    keywords_alt.No Args Alt    1

    # incorrect use
    keywords.Args Alt
    keywords.No Args Alt    1
    keywords_alt.Args Alt    1
    keywords_alt.No Args Alt

    # ambiguous - should be ignored
    Args Alt
    Args Alt    1
    No Args Alt
    No Args Alt    1
