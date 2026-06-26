*** Variables ***
${EMPTY_SCALAR}     ${EMPTY}
@{EMPTY_LIST}       @{EMPTY}
&{EMPTY_DICT}       &{EMPTY}


*** Test Cases ***
Test With Empty Vars
    VAR    ${empty_in_test}    ${EMPTY}
    VAR    @{empty_list_test}    @{EMPTY}
    Log    ${empty_in_test}


*** Keywords ***
Keyword With Empty Vars
    VAR    ${empty_in_kw}    ${EMPTY}
    VAR    &{empty_dict_kw}    &{EMPTY}
    Log    ${empty_in_kw}
