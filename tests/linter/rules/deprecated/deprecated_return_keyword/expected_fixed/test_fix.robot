*** Test Cases ***
Return From Keyword Example
    [Arguments]    ${element}    @{items}
    ${index} =    Set Variable    ${0}
    FOR    ${item}    IN    @{items}
        ${index} =    Set Variable    ${index + 1}
        IF    ${index} == ${5}
            RETURN    ${index}
        END
    END
    RETURN    ${-1}    # Some comment


*** Keywords ***
Multiline And Extra Line
    RETURN
    ...    ${value}    ${value2}
    IF    ${condition}
        RETURN    value
    END


For Loop
    ${var}    Set Variable    1
    FOR    ${variable}  IN  1  2
        IF    ${var}==2
            RETURN    Keyword 2    ${var}
        END
        Log    ${variable}
    END

With IF
    ${var}    Set Variable    1
    IF    ${var}>0
        IF    $var
            RETURN    Some Keyword    ${var}    1
        END
    END

Missing condition
    Return From Keyword If

Empty return
    IF    ${condition}
        RETURN
    END
    RETURN

Existing RETURN
    RETURN
    RETURN
