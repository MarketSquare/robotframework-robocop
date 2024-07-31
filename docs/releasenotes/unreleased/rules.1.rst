Allow to ignore run keywords in misaligned-continuation-row rule (#1065)
------------------------------------------------------------------------

W1015 ``misaligned-continuation-row`` detects if statements have misaligned rows::

    *** Keywords ***
    Misaligned example
        Keyword Call
        ...    first argument
        ...  second argument  # should be executed

This rules contradicts with how Robotidy aligns nested keywords with ``IndentNestedKeywords`` tranformer to provide
extra alignment for readability purposes::

    SSH Wait For Device To Close SSH
        [Documentation]    Wait until SSH connection is closed by device.
        Wait Until Keyword Succeeds    2min    2s
        ...    Run Keyword And Expect Error    SSHException: SSH session not active
        ...        SSH Log FW Version    level=DEBUG

It is now possible to ignore run keywords by setting ignore_run_keywords to True::

    robocop -c misaligned-continuation-row:ignore_run_keywords:True src

By default it is disabled and run keywords are not ignored.
