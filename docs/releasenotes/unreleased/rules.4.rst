Variable not used from Variables section (#1002)
------------------------------------------------

Variables defined in ``*** Variables ***`` section in test/task file and not used within the file are now reported
with I0920 ``unused-variable`` rule:

```
*** Variables ***
${GLOBAL_USED}    value
${GLOBAL_NOT_USED}    value  # will be reported in Robocop
${GLOBAL_USED_IN_SECTION}    value
${GLOBAL_USED2}    value with ${GLOBAL_USED_IN_SECTION}


*** Test Cases ****
Test
    [Documentation]    Use one global variable and call keyword that uses second.
    Log    ${GLOBAL_USED}
    Keyword


*** Keywords ***
Keyword
    [Documentation]    Use second global variable.
    Log    ${GLOBAL_USED2}

```
