*** Test Cases ***
Overwrite reserved with VAR
    VAR     ${TEST_NAME}    new_value
    VAR    ${TEST DOCUMENTATION}    new value    scope=GLOBAL
    VAR    ${LOG LEVEL}    ${OPTIONS}    scope=LOCAL


*** Keywords ***
Overwrite reserved with VAR
    VAR     ${TEST_NAME}    new_value
    VAR    ${TEST DOCUMENTATION}    new value    scope=GLOBAL
    VAR    ${LOG LEVEL}    ${OPTIONS}    scope=LOCAL
