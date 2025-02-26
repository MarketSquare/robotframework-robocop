*** Settings ***
Test Template       Login with invalid credentials should fail


*** Test Cases ***                  USERNAME            PASSWORD
Invalid User Name                   [Tags]              foo
                                    invalid             ${VALID PASSWORD}
Invalid Password
                                    [Tags]              bar
                                    ${VALID USER}       invalid
Invalid User Name and Password      [Tags]              baz
                                    invalid             invalid
Empty User Name                     ${EMPTY}            ${VALID PASSWORD}
Empty Password                      [Tags]              spam                    eggs
                                    ${VALID USER}       ${EMPTY}
Empty User Name and Password        ${EMPTY}            ${EMPTY}


*** Keywords ***
Login With Invalid Credentials Should Fail
    [Arguments]    ${username}    ${password}
