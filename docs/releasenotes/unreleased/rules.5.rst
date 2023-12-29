New rule replace-set-variable-with-var (#973)
---------------------------------------------

Added new I0327 ``replace-set-variable-with-var`` rule.

Starting from Robot Framework 7.0, it is possible to create variables inside tests and user keywords using the VAR
syntax. The VAR syntax is recommended over previously existing keywords. Starting from RF 7.0 Robocop will report
new issue when ``Set Variable`` type of keyword is used.

Example with Set Variable keywords::

    *** Keywords ***
    Set Variables To Different Scopes
        Set Local Variable    ${local}    value
        Set Test Variable    ${TEST_VAR}    value
        Set Task Variable    ${TASK_VAR}    value
        Set Suite Variable    ${SUITE_VAR}    value
        Set Global Variable    ${GLOBAL_VAR}    value

Can be now rewritten to::

    *** Keywords ***
    Set Variables To Different Scopes
        VAR    ${local}    value
        VAR    ${TEST_VAR}    value    scope=TEST
        VAR    ${TASK_VAR}    value    scope=TASK
        VAR    ${SUITE_VAR}    value    scope=SUITE
        VAR    ${GLOBAL_VAR}    value    scope=GLOBAL
