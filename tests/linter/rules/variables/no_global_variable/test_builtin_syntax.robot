*** Variables ***
${amazing}    Hello world!

*** Test Cases ***
Test
    ${amazing} =    Set Variable    Hello universe
    Set Global Variable    ${amazing}

Using BuiltIn library prefix
    ${amazing} =    Set Variable    Hello universe
    BuiltIn.Set Global Variable    ${amazing}

Using underscores
    ${amazing} =    Set Variable    Hello universe
    Set_Global_Variable    ${amazing}

*** Keywords ***
Keyword
    ${amazing} =    Set Variable    Hello universe
    Set Global Variable    ${amazing}
