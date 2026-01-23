*** Test Cases ***
Variables with item access should be ignored
    VAR    &{dict}=    a=1    b=2    c=3
    ${dict}[a]=    Set Variable    0
    ${container}    Get Container
    ${container.item}    Set Variable    0
    ${list}[0] =       Set Variable     first
    ${list}[${1}] =    Set Variable     second
    ${list}[2:3] =     Create List      third
    ${container.item}    ${container.item2}    Set Variable    4    5
    ${var}    ${container.item2}    Set Variable    4    5
