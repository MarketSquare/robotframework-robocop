*** Variables ***
${amazing}    Hello world!

*** Test Cases ***
Test
    ${amazing} =    Set Variable    Hello universe
    Set Suite Variable    ${amazing}

Using BuiltIn library prefix
    ${amazing} =    Set Variable    Hello universe
    BuiltIn.Set Suite Variable    ${amazing}

Using underscores
    ${amazing} =    Set Variable    Hello universe
    Set_Suite_Variable    ${amazing}

*** Keywords ***
Keyword
    ${amazing} =    Set Variable    Hello universe
    Set Suite Variable    ${amazing}
