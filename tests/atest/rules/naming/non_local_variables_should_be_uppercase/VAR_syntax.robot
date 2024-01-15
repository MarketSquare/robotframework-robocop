*** Keywords ***
VAR syntax
    VAR    ${suite}    value    scope=SUITE
    VAR    ${global}    value    scope=GLOBAL
    VAR    ${test}    value    scope=TEST
    VAR    ${task}    value    scope=TASK
    VAR    ${local_default}    value    scope=local
    VAR    ${local_default}    value
    VAR    ${SUITE}    value    scope=SUITE
    VAR    ${GLOBAL}    value    scope=GLOBAL
    VAR    ${TEST}    value    scope=TEST
    VAR    ${TASK}    value    scope=TASK
    VAR    ${LOCAL_DEFAULT}    value    scope=local
    VAR    ${LOCAL_DEFAULT}    value
    VAR    ${nested_${TEST}}    value    scope=TEST
    VAR    ${NESTED_${TEST}}    value    scope=TEST
    VAR    ${invalid
