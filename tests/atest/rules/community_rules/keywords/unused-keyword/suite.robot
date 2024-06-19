*** Keywords ***
Used Keyword
    Used Keyword 2    ${arg}
    FOR    ${var}  IN RANGE  10
        Used Keyword 3    ${var}
    END

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


*** Test Cases ***
Test cases are last for testing purposes
    Used_Keyword
