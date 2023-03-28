*** Settings ***
Documentation       Templated suite with cases from #758 bug
Test Template       Login with invalid credentials should fail


*** Test Cases ***                  USERNAME            PASSWORD
Invalid User Name                   [Tags]              foo
                                    invalid             ${VALID PASSWORD}
Invalid Password                    [Documentation]     foo
                                    [Tags]              bar
                                    ${VALID USER}       invalid
Invalid User Name and Password      [Tags]              baz
                                    invalid             invalid
Empty User Name
                                    ${EMPTY}            ${VALID PASSWORD}
Empty Password                      ${VALID USER}       ${EMPTY}
                                    [Tags]              spam  eggs
Empty User Name and Password        ${EMPTY}            ${EMPTY}
# Wrong cases below
Invalid User Name                   [Tags]              foo
                   invalid             ${VALID PASSWORD}
Invalid Password                    [Documentation]     foo
                                    [Tags]              bar
                                    ${VALID USER}       invalid
Invalid User Name and Password      [Tags]              baz
      nvalid             invalid
Empty User Name
                                    ${EMPTY}            ${VALID PASSWORD}
Empty Password                      ${VALID USER}       ${EMPTY}
                      [Tags]              spam  eggs
Empty User Name and Password        ${EMPTY}            ${EMPTY}


*** Keywords ***
Login With Invalid Credentials Should Fail
    [Documentation]    Templated keyword
    [Arguments]    ${username}    ${password}
    No Operation
