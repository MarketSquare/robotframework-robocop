*** Keywords ***
    [Arguments]    ${element}    @{items}
    ${index} =    Set Variable    ${0}
    FOR    ${item}    IN    @{items}
        ${index} =    Set Variable    ${index + 1}
        IF    ${index} == ${5}
            Return From Keyword    ${index}
        END
    END
    Return From Keyword    ${-1}    # Could also use [Return]
