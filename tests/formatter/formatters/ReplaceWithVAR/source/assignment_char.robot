*** Test Cases ***
Match original assignment
    ${value}    IF    ${condition}    Set Variable    value    ELSE    Set Variable    ${None}
    ${value}=    IF    ${condition}    Set Variable    value    ELSE    Set Variable    ${None}
    ${value} =    IF    ${condition}    Set Variable    value    ELSE    Set Variable    ${None}

Inline IF mixed set variable and custom keyword
    ${value}=    IF    ${condition}    Set Variable    value    ELSE IF  False    Custom Keyword    ELSE    Set Variable    ${None}

Inline IF set with two assign two args
    ${many}    ${vars} =    IF    True   Set Variable    value    value

Catenate
    ${assign}=    Catenate    SEPARATOR=    first

Create Dictionary
    ${dict}=    Create Dictionary    key=value
        ...    key2=value  # comment
