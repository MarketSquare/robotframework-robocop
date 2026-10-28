*** Test Cases ***
Test
    Set Local Variable    ${my_var}    0
    Set Local Variable    ${my var}    0
    Set Local Variable    ${MY_VAR}    1
    Set Suite Variable    ${my_var}    0


*** Keywords ***
Some Keyword
    Set Local Variable    ${my_var}    0
    Set Local Variable    $escaped    0
    Set Local Variable    \${escaped}    0
    Set Local Variable    invalid    0
    Set Local Variable
    ...
    ...    previous arg is empty now
    Set Local Variable    ${${var}Front Nesting}    0
