*** Test Cases ***
Test With Overwritten Variables
    ${my_var}  Set Variable  1
    ${MY VAR}  Set Variable  2
    ${myVar}   Set Variable  3
    ${another_var}   Set Variable  4
    ${MYVAR}   Set Variable  5
    ${M Y V A R}   Set Variable  6


*** Keywords ***
Keyword With Overwritten Variables
    ${someVar}   Set Variable  1
    ${SOME_VAR}  Set Variable  2
    ${myvar}     Set Variable  3
