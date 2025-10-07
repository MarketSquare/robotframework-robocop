*** Test Cases ***
Name change with scope
    ${return_var}    Keyword
    VAR    ${variable}    ${return_var}
    ${return_var}    Overwrite Keyword
    VAR    ${return_var}    value    scope=local
    VAR    ${RETURN_VAR}    value    scope=TEST
    VAR    ${RETURN_VAR}    value    scope=SUITE
    VAR    ${RETURN_VAR}    value    scope=SUITES
    VAR    ${RETURN_VAR}    value    scope=GLOBAL
    Log    ${RETURN_VAR}
    VAR    ${variable}    value    scope=local
    VAR    &{SOME_DICT}    &{some_dict}    scope=TEST
