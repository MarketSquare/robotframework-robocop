*** Variables ***
${EMPTY_SCALAR}     ${EMPTY}
@{EMPTY_LIST}       @{EMPTY}
&{EMPTY_DICT}       &{EMPTY}


*** Test Cases ***
Test With Empty Vars
    VAR    ${empty_in_test}
    VAR    @{empty_list_test}
    Log    ${empty_in_test}


*** Keywords ***
Keyword With Empty Vars
    VAR    ${empty_in_kw}
    VAR    &{empty_dict_kw}
    Log    ${empty_in_kw}
