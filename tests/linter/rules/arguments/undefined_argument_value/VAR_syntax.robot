*** Test Cases ***
VAR without =
    VAR    ${name}    value
    VAR    ${name}    scope=SUITE

VAR with = in name
    VAR    ${name}=    value
    VAR    ${name}=    scope=SUITE
    VAR    ${name2} =    value    scope=SUITE

VAR with undefined argument value
    VAR    ${name}    value=
    VAR    ${name}=    value=
