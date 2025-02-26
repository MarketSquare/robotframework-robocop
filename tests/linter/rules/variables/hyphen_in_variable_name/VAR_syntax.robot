*** Test Cases ***
My Test Case
    VAR    ${r}   ${2-1}  # this is fine
    VAR    ${a-b}    1  # this will warn - because if it's later used as ${a-b} it can lead to ambiguous results
    VAR    ${a\-b}  1  # this will warn
    VAR    ${-}    1   scope=GLOBAL  # this will warn
    VAR    ${a-}   1   # this will warn
    VAR    ${-b}   1   # this will warn
