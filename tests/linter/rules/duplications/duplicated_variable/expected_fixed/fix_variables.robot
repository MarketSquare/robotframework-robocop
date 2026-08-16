*** Variables ***
${VAR}    first
# ignored duplicate
${OTHER}    value
${MULTI}    1
...    2


*** Test Cases ***
Test
    Log    ${VAR}
