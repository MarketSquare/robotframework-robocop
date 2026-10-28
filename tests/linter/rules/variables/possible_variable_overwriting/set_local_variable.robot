*** Test Cases ***
Test With Overwritten Local Variables
    Set Local Variable    ${my_var}    0
    Set Local Variable    ${MY VAR}    1
    Set Local Variable    ${my_var}    2
    Set Suite Variable    ${MY_VAR}    3


*** Keywords ***
Keyword With Overwritten Local Variables
    ${my_var}    Set Variable    0
    Set Local Variable    ${MyVar}    1

Keyword With Non Local Variables
    Set Suite Variable    ${my_var}    0
    Set Test Variable    ${MY VAR}    1

Keyword With Invalid Set Local Variable
    Set Local Variable    invalid    0
    Set Local Variable    $escaped    0
    Set Local Variable
    ...
    ...    previous arg is empty now
