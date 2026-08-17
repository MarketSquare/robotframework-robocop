*** Keywords ***
Used Keyword
    Used Keyword 2    ${arg}
    FOR    ${var}  IN RANGE  10
        Used Keyword 3    ${var}
    END
    Embedded word
    Embedded word 1
    Embedded Inside Keyword

Used Keyword 2
    [Arguments]    ${arg}
    Log    ${arg}

Used Keyword 3
    [Arguments]    ${arg}
    Used Keyword 2    ${arg}

Not Used Keyword
    Nested Not Used Keyword

Nested Not Used Keyword  # it should be reported in the future since parent keyword is not used
    Log    ${TEST_NAME}

Embedded ${variable}
    No Operation

Embedded ${variable} ${numbers:\d+}
    No Operation

Embedded ${inside} Keyword
    No Operation

Embedded ${not} Used
    No Operation

Used In Setup
    No Operation

Used In Teardown
    No Operation

Used In Timeout
    No Operation

Used In Run Keyword
    No Operation

Used In Wait Until Keyword
    No Operation

Used With BDD
    No Operation

Used With BDD 2
    No Operation

Used With BDD 3
    No Operation

Used With BDD 4
    No Operation

*** Test Cases ***
Test cases are last for testing purposes
    Used_Keyword

Test with settings
    [Setup]    Used In Setup
    [Template]    Used In Timeout
    [Teardown]    Used In Teardown

Test with run keywords
    Run Keywords    Used Keyword
    ...    AND
    ...    Used In Run Keyword

    Then Wait Until Keyword Succeeds    10x    500ms    Used In Wait Until Keyword

BDD
   Given Used With BDD
   When Used With BDD 2
   And Used With BDD 3
   Then Used With BDD 4
