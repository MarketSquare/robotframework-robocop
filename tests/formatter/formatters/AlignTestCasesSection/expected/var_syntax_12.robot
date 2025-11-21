*** Test Cases ***
VAR with =
    VAR         ${var_1}=               My value 1
    VAR         ${var_2}=               My value 2
    GoTo        ${URL}
    Click       Cancel

VAR without =
    VAR         ${var_1}                My value 1
    VAR         ${var_2}                My value 2
    GoTo        ${URL}
    Click       Cancel

VAR with long variable names
    VAR         ${variable_name_that_affects_something}                 My value 1
    VAR         ${var_2}                My value 2
    GoTo        ${URL}
    Click       Cancel

VAR with long variable names and long keyword name
    VAR         ${variable_name_that_affects_something}                 My value 1
    VAR         ${var_2}                My value 2
    Click On The Button And Input Text Into Field       ${URL}
    Click       Cancel

VAR without value
    VAR         ${var_1}
    Should Be Equal                     ${c}            123

VAR with errors
    VAR
    VAR    ${var
    VAR    $var    value
    Should Be Equal                     ${c}            123

VAR multiline
    VAR         ${var}
    ...         value
    Should Be Equal                     ${c}            123

Only VAR
    VAR    ${a}    ${1}
