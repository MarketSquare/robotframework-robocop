*** Keywords ***
Keyword with [Return]
    No Operation

    [Arguments]    ${element}    @{items}
    ${index} =    Set Variable    ${0}
    FOR    ${item}    IN    @{items}
        ${index} =    Set Variable    ${index + 1}
        # robocop: fmt: off
        IF    ${index} == ${5}
            RETURN    ${index}
        END
    END
    # robocop: fmt: off
    RETURN    ${-1}    # Could also use [Return]
    RETURN    1  # robocop: fmt: off

First
    ${var}    Set Variable    1
    IF    ${var}==2
        RETURN    ${var}  # robocop: fmt: off
    END
    FOR    ${variable}  IN  1  2
        Log    ${variable}
    END
