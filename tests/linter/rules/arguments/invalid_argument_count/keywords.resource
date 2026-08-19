*** Keywords ***
Login
    [Arguments]    ${username}    ${password}
    Log    ${username}

With Default
    [Arguments]    ${a}    ${b}=2
    Log    ${a}

With Varargs
    [Arguments]    ${a}    @{rest}
    Log    ${a}

With Kwargs
    [Arguments]    ${a}    &{opts}
    Log    ${a}

No Args
    Log    hello

Embedded ${name} Keyword
    Log    ${name}

Named Only
    [Arguments]    ${a}    @{}    ${strict}
    Log    ${a}

Args Alt
    [Arguments]    ${arg}
    Log    ${arg}

No Args Alt
    Log    hello
