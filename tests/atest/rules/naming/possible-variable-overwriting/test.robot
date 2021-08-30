*** Test Cases ***
Test With Overwritten Variables
    ${my_var}       Set Variable    1
    ${my_var}       Set Variable    2
    ${MY VAR}       Set Variable    2
    ${myVar}        Set Variable    3
    ${another_var}  Set Variable    4
    ${MYVAR}        Set Variable    5
    ${M Y V A R}    Set Variable    6
    ${mYvAr}        Some Keyword    123


*** Keywords ***
Keyword With Overwritten Variables
    [Arguments]     ${my_var}
    ${someVar}      Set Variable    1
    ${SOME_VAR}     Set Variable    2
    ${myvar}        Set Variable    3
    ${myvar}        Set Variable    4
    ${somevar}      ${some var}     Return Two Values

Keyword With Different Types Of Variables
    [Arguments]     ${simple_var}
    ${simple_var}   Set Variable        1
    ${simpleVar}    Set Variable        2
    @{SIMPLE_VAR}   Create List         1    2    3
    &{SIMPLE_VAR}   Create Dictionary   a=1  b=2  c=3
