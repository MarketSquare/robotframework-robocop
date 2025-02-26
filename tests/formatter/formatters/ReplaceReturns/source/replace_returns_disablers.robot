*** Keywords ***
Keyword with [Return]
    [Return]    1  # robotidy: off
    No Operation

    [Arguments]    ${element}    @{items}
    ${index} =    Set Variable    ${0}
    FOR    ${item}    IN    @{items}
        ${index} =    Set Variable    ${index + 1}
        # robotidy: off
        IF    ${index} == ${5}
            Return From Keyword    ${index}
        END
    END
    # robotidy: off
    Return From Keyword    ${-1}    # Could also use [Return]

First
    ${var}    Set Variable    1
    Return From Keyword_If    ${var}==2               ${var}  # robotidy: off
    FOR    ${variable}  IN  1  2
        Log    ${variable}
    END
