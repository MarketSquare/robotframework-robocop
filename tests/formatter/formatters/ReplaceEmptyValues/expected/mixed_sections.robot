*** Variables ***
${VAR_EMPTY}    ${EMPTY}
@{VAR_LIST}     @{EMPTY}


*** Test Cases ***
Test Should Not Be Modified
    VAR    ${empty_in_test}
    Log    ${empty_in_test}


*** Keywords ***
Keyword With Empty Vars
    VAR    ${empty_in_kw}    ${EMPTY}
    Log    ${empty_in_kw}
