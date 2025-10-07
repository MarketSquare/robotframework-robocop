*** Test Cases ***
Robocop disabler in last line - VAR
    VAR    ${x}
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline  # robocop: off=line-too-long

Robocop disabler in first line - VAR
    VAR    ${x}  # robocop: off=line-too-long
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline

Robocop disabler in last line - Keyword
    Keyword    ${x}
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline  # robocop: off=line-too-long

Robocop disabler in first line - Keyword
    Keyword    ${x}  # robocop: off=line-too-long
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline

Two disablers in VAR
    VAR    ${x}  # robocop: off=some-rule
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline  # robocop: off=line-too-long

Two disablers in Keyword
    Keyword    ${x}  # robocop: off=some-rule
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline  # robocop: off=line-too-long

Mixed comments
    VAR    ${x}  # robocop: off=some-rule
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline  # some comment
    VAR    ${x}  # some comment
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline  # robocop: off=line-too-long
    Single Keyword
    ...    arg  # robocop: off=some-rule
    Single Keyword  # robocop: off=some-rule
    ...    arg
