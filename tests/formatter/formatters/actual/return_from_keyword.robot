*** Keywords ***
    [Arguments]    ${element}    @{items}
    ${index} =    Set Variable    ${0}
    FOR    ${item}    IN    @{items}
        ${index} =    Set Variable    ${index + 1}
        IF    ${index} == ${5}
            RETURN    ${index}
        END
    END
    RETURN    ${-1}    # Could also use [Return]
