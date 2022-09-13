*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One_More

Test Underscore
    Embedded Keyword With ${variable_with_underscore}

*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail

Embedded Keyword With ${variable_with_underscore}
    Log    ${variable_with_underscore}

Run Keywords
    Run Keyword If    ${condition}
    ...    Run_keywords
    ...        Name    ${arg}    AND
    ...        _Underscore    1    AND
    ...        Under_sc ore
