*** Keywords ***
Keyword with [Return]

    No Operation
    RETURN    1  # it can be first

Keyword with Multiple [Return] And Empty Lines
    [Documentation]    First one will be changed to RETURN, second ignored (handled by different rule).
    Step 1
    [Return]    2
    Step 2
    RETURN    1



Keyword with RETURN
    No Operation
    RETURN    1

Keyword With Two RETURN
    IF    ${GLOBAL}    RETURN
    No Operation
    RETURN

Keyword With Multiline Return Setting
    Keyword
    RETURN    1
    ...    2

Keyword With Mixed RETURN
    IF    ${condition}
        RETURN    2  # conditional return
    END
    RETURN    1  # sets default return

Keyword With Mixed RETURN 2
    First Keyword
    [Return]    1    # shall be ignored
    RETURN    2

Two Keywords Without New Lines
    Keyword
    RETURN    ${value}
Two Keywords Without New Lines
    Keyword
    RETURN    ${value}

Multiple duplications
    [Arguments]    ${a1}    ${a2}    ${a3}
    [Arguments]    ${arg}
    [Documentation]
    [Documentation]    K1
    [Documentation]    K2
    [Tags]    K1
    [Tags]    K2
    [Timeout]
    [Timeout]    1s
    [Timeout]    2s
    No Operation
    [Return]    R1
    [Return]    R2
    [Return]    R3
    RETURN    R0
