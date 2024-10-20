*** Keywords ***
Keyword with run keyword
    Other Keyword
    ...    first argument
    ...        second argument
    Other Keyword 2
    ...    first argument
    ...    second argument
    Wait Until Keyword Succeeds    2min    2s
    ...    Run Keyword And Expect Error    SSHException: SSH session not active
    ...        SSH Log FW Version    level=DEBUG
