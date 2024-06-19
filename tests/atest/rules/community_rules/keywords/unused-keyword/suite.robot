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


*** Test Cases ***
Test cases are last for testing purposes
    Used_Keyword
