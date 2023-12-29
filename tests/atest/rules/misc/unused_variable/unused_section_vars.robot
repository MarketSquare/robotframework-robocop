*** Settings ***
Documentation    Global variables in test/task files cannot be imported and should be used within file.


*** Variables ***
${GLOBAL_USED}    value
${GLOBAL_NOT_USED}    value
${GLOBAL_USED_IN_SECTION}    value
${GLOBAL_USED2}    value with ${GLOBAL_USED_IN_SECTION}


*** Test Cases ****
Test
    [Documentation]    Use one global variable and call keyword that uses second.
    Log    ${GLOBAL_USED}
    Keyword


*** Keywords ***
Keyword
    [Documentation]    Use second global variable.
    Log    ${GLOBAL_USED2}
