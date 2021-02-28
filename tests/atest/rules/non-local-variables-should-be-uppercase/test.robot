*** Test Cases ***
Test
    Set Task Variable  ${my_var}  1
    Set Suite Variable  ${my var}  1
    Set Test Variable  ${My Var}  1
    Set Global Variable  ${My_Var}  1
    Set Task Variable  ${MY_VAR}  1
    Set Suite Variable  ${MY VAR}  1
    Set Test Variable  ${MY_VAR}  1
    Set Global Variable  ${MY VAR}  1


*** Keywords ***
Some Keyword
    Set Task Variable  ${my_var}  1
    Set Suite Variable  ${my var}  1
    Set Test Variable  ${My Var}  1
    Set Global Variable  ${My_Var}  1
    Set Task Variable  ${MY_VAR}  1
    Set Suite Variable  ${MY VAR}  1
    Set Test Variable  ${MY_VAR}  1
    Set Global Variable  ${MY VAR}  1
