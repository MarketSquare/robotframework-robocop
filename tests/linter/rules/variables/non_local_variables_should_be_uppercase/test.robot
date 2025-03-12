*** Test Cases ***
Test
    Set Task Variable  ${my_var}  0
    Set Suite Variable  ${my var}  0
    Set Test Variable  ${My Var}  0
    Set Global Variable  ${My_Var}  0
    Set Task Variable  ${MY_VAR}  1
    Set Suite Variable  ${MY VAR}  1
    Set Test Variable  ${MY_VAR}  1
    Set Global Variable  ${MY VAR}  1


*** Keywords ***
Some Keyword
    Set Task Variable  ${my_var}  0
    Set Suite Variable  ${my var}  0
    Set Test Variable  ${My Var}  0
    Set Global Variable  ${My_Var}  0
    Set Task Variable  ${MY_VAR}  1
    Set Suite Variable  ${MY VAR}  1
    Set Test Variable  ${MY_VAR}  1
    Set Global Variable  ${MY VAR}  1
    Set Global Variable
    ...
    ...    previous arg is empty now
    Set Test Variable  $escaped  1
    Set Task Variable  $escaped  0
    Set Suite Variable  $escaped  1
    Set Global Variable  $escaped  1
    Set Test Variable  \${escaped}  1
    Set Task Variable  \${escaped}  0
    Set Suite Variable  \${escaped}  1
    Set Global Variable  \${escaped}  1
    Set Test Variable  invalid  1
    Set Task Variable  invalid  0
    Set Suite Variable  invalid  1
    Set Global Variable  invalid  1

Keyword With Nested Variables
    Set Task Variable  ${${var@{var}}multiple_nestings&{var}}  0
    Set Suite Variable  ${nesting at the end${VAR}}  0
    Set Test Variable  ${${var}Front Nesting}  0
    Set Global Variable  ${Middle_${var}_Nesting}  0
    Set Task Variable  ${CAPITAL_${var}}  1
    Set Suite Variable  ${CAPITAL SPACE @{var}}  1
    Set Test Variable  ${CAPITAL_&{VAR}}  1
    Set Global Variable  ${${Var} MY VAR}  1
    Set Global Variable  ${${Var} TWO VARS${var}}  1
    Set Global Variable  ${${Var} TWO VARS${var} AFTER}  1
    Set Global Variable     ${${name}}      "My variable value"
