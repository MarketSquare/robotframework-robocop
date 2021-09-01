*** Test Cases ***
My Test Case
    ${r}    Set Variable  ${2-1}  # this is fine
    ${a-b}  Set Variable  1     # this will warn - because if it's later used as ${a-b} it can lead to ambiguous results
    ${a\-b}  Set Variable  1    # this will warn - because if it's later used as ${a-b} it can lead to ambiguous results
    ${-}    Set Variable  1     # this will warn - because if it's later used as ${a-b} it can lead to ambiguous results
    ${a-}   Set Variable  1     # this will warn - because if it's later used as ${a-b} it can lead to ambiguous results
    ${-b}   Set Variable  1     # this will warn - because if it's later used as ${a-b} it can lead to ambiguous results
    My Keyword    1  2  3


*** Keywords ***
My Keyword
    ${r}    Set Variable  ${2-1}  # this is fine
    ${a-b}  Set Variable  1     # this will warn - because if it's later used as ${a-b} it can lead to ambiguous results
    ${a\-b}  Set Variable  1    # this will warn - because if it's later used as ${a-b} it can lead to ambiguous results
    ${-}    Set Variable  1     # this will warn - because if it's later used as ${a-b} it can lead to ambiguous results
    ${a-}   Set Variable  1     # this will warn - because if it's later used as ${a-b} it can lead to ambiguous results
    ${-b}   Set Variable  1     # this will warn - because if it's later used as ${a-b} it can lead to ambiguous results
