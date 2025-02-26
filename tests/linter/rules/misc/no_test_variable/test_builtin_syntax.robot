*** Variables ***
${amazing}    Hello world!

*** Test Cases ***
Test
    ${amazing} =    Set Variable    Hello universe
    Set Test Variable    ${amazing}

Using BuiltIn library prefix
    ${amazing} =    Set Variable    Hello universe
    BuiltIn.Set Test Variable    ${amazing}

Using underscores
    ${amazing} =    Set Variable    Hello universe
    Set_Test_Variable    ${amazing}

Using task
    ${amazing} =    Set Variable    Hello universe
    Set Task Variable    ${amazing}

*** Keywords ***
Keyword
    ${amazing} =    Set Variable    Hello universe
    Set Test Variable    ${amazing}
