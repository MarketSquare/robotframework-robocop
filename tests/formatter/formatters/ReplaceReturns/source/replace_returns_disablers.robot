*** Keywords ***
Keyword with [Return]
    [Return]    1  # robocop: fmt: off
    No Operation

    [Arguments]    ${element}    @{items}
    ${index} =    Set Variable    ${0}
    FOR    ${item}    IN    @{items}
        ${index} =    Set Variable    ${index + 1}
        # robocop: fmt: off
        IF    ${index} == ${5}
            Return From Keyword    ${index}
        END
    END
    # robocop: fmt: off
    Return From Keyword    ${-1}    # Could also use [Return]

First
    ${var}    Set Variable    1
    Return From Keyword_If    ${var}==2               ${var}  # robocop: fmt: off
    FOR    ${variable}  IN  1  2
        Log    ${variable}
    END
