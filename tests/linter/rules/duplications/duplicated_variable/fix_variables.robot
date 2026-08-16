*** Variables ***
${VAR}    first
${var}    second  # ignored duplicate
@{V_AR}    a    b
${OTHER}    value
${MULTI}    1
...    2
${multi}    3
...    4


*** Test Cases ***
Test
    Log    ${VAR}
