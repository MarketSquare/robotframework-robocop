*** Test Cases ***
Test With Empty Vars
    VAR    ${empty_scalar}    ${EMPTY}
    VAR    @{empty_list}    @{EMPTY}
    VAR    &{empty_dict}    &{EMPTY}
    VAR    ${empty_scalar_cont}
    ...    ${EMPTY}
    VAR    ${scalar}    value
    Log    ${empty_scalar}

Test With Scoped VAR
    VAR    ${empty_test}    ${EMPTY}    scope=TEST
    VAR    ${empty_suite}    ${EMPTY}    scope=SUITE
    VAR    ${empty_global}    ${EMPTY}    scope=GLOBAL
    VAR    @{empty_list}    @{EMPTY}    scope=TEST
    Log    ${empty_test}

Test Traditional Assignment
    ${empty}    Set Variable
    ${filled}    Set Variable    value
    Log    ${empty}
