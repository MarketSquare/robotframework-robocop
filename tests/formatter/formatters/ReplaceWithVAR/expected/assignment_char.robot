*** Test Cases ***
Match original assignment
    IF    ${condition}
        VAR    ${value}    value
    ELSE
        VAR    ${value}    ${None}
    END
    IF    ${condition}
        VAR    ${value}=    value
    ELSE
        VAR    ${value}=    ${None}
    END
    IF    ${condition}
        VAR    ${value} =    value
    ELSE
        VAR    ${value} =    ${None}
    END

Inline IF mixed set variable and custom keyword
    IF    ${condition}
        VAR    ${value}=    value
    ELSE IF    False
        ${value}=    Custom Keyword
    ELSE
        VAR    ${value}=    ${None}
    END

Inline IF set with two assign two args
    IF    True
        VAR    ${many}    value
        VAR    ${vars} =    value
    END

Catenate
    VAR    ${assign}=    first    separator=${EMPTY}

Create Dictionary
    VAR    &{dict}=    key=value    key2=value  # comment
