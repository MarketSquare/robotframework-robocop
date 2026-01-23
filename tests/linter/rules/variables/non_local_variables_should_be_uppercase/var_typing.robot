*** Test Cases ***
Set report
    Set Task Variable  ${my_var: int}  0
    Set Suite Variable  ${my var: list[str]}  0
    Set Test Variable  ${My Var: Enum}  0
    Set Global Variable  ${My_Var: str}  0

Set ignore
    Set Task Variable  ${MY_VAR: int}  1
    Set Suite Variable  ${MY VAR: list[str]}  1
    Set Test Variable  ${MY_VAR: Enum}  1
    Set Global Variable  ${MY VAR: str}  1

VAR report
    VAR    ${suite: int}    value    scope=SUITE
    VAR    ${global: list[str]}    value    scope=GLOBAL
    VAR    ${test: Enum}    value    scope=TEST
    VAR    ${task: str}    value    scope=TASK

VAR ignore
    VAR    ${SUITE: int}    value    scope=SUITE
    VAR    ${GLOBAL: list[str]}    value    scope=GLOBAL
    VAR    ${TEST: Enum}    value    scope=TEST
    VAR    ${TASK: str}    value    scope=TASK
