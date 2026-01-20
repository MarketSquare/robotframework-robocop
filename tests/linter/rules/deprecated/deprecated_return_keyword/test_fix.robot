*** Test Cases ***
Return From Keyword Example
    [Arguments]    ${element}    @{items}
    ${index} =    Set Variable    ${0}
    FOR    ${item}    IN    @{items}
        ${index} =    Set Variable    ${index + 1}
        IF    ${index} == ${5}
            Return From Keyword    ${index}
        END
    END
    Return From Keyword    ${-1}    # Some comment


*** Keywords ***
Multiline And Extra Line
    BuiltIn.Return From Keyword
    ...    ${value}    ${value2}
    Return From Keyword If
    ...    ${condition}
    ...    value


For Loop
    ${var}    Set Variable    1
    FOR    ${variable}  IN  1  2
        BuiltIn.Return From Keyword If    ${var}==2  Keyword 2    ${var}
        Log    ${variable}
    END

With IF
    ${var}    Set Variable    1
    IF    ${var}>0
        Return From Keyword If    $var    Some Keyword    ${var}
          ...  1
    END

Missing condition
    Return From Keyword If

Empty return
    Return From Keyword If    ${condition}
    Return From Keyword

Existing RETURN
    Return From Keyword
    RETURN
