*** Test Cases ***
Robocop disabler in last line - VAR
    VAR    ${x}  # robocop: off=line-too-long
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline

Robocop disabler in first line - VAR
    VAR    ${x}  # robocop: off=line-too-long
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline

Robocop disabler in last line - Keyword
    Keyword  # robocop: off=line-too-long
    ...    ${x}
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline

Robocop disabler in first line - Keyword
    Keyword  # robocop: off=line-too-long
    ...    ${x}
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline

Two disablers in VAR
    VAR    ${x}  # robocop: off=some-rule robocop: off=line-too-long
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline

Two disablers in Keyword
    Keyword  # robocop: off=some-rule robocop: off=line-too-long
    ...    ${x}
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline

Mixed comments
    VAR    ${x}  # robocop: off=some-rule some comment
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline
    VAR    ${x}  # some comment robocop: off=line-too-long
    ...    verylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylonglineverylongline
    Single Keyword
    ...    arg  # robocop: off=some-rule
    Single Keyword  # robocop: off=some-rule
    ...    arg
