*** Test Cases ***
Test With Empty Vars
    VAR    ${empty_scalar}
    VAR    @{empty_list}
    VAR    &{empty_dict}
    VAR    ${empty_scalar_cont}
    ...
    VAR    ${scalar}    value
    Log    ${empty_scalar}

Test With Scoped VAR
    VAR    ${empty_test}    scope=TEST
    VAR    ${empty_suite}    scope=SUITE
    VAR    ${empty_global}    scope=GLOBAL
    VAR    @{empty_list}    scope=TEST
    Log    ${empty_test}

Test Traditional Assignment
    ${empty}    Set Variable
    ${filled}    Set Variable    value
    Log    ${empty}
