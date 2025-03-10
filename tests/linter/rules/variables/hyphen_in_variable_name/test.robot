*** Variables ***
${A}    correct
${A-B}    incorrect


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

Keyword With Dict And List Item Assignments
    ${list} =    Create List    one    two    three    four
    ${list}[0] =    Set Variable    first
    ${list}[${1}] =    Set Variable    second
    ${list}[2:3] =    Evaluate    ['third']
    ${list}[-1] =    Set Variable    last

    ${DICTIONARY} =    Create Dictionary    first_name=unknown
    ${DICTIONARY}[first_name] =    Set Variable    John
    ${DICTIONARY}[last-name] =    Set Variable    Doe

Invalid Item Assignment
    ${DICTIONARY    Create Dictionary    first_name=John

In Arguments
    [Arguments]    ${correct}    ${in-correct}
