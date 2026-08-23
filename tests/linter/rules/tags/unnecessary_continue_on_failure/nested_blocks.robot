*** Test Cases ***
Nested Blocks
    [Tags]    robot:continue-on-failure
    FOR    ${index}    IN RANGE    3
        Run Keyword And Continue On Failure    Assert A
    END
    IF    $condition
        Run Keyword And Continue On Failure    Assert B
    ELSE
        Run Keyword And Continue On Failure    Assert C
    END
    WHILE    $condition
        Run Keyword And Continue On Failure    Assert D
    END
    TRY
        Run Keyword And Continue On Failure    Assert E
    EXCEPT    Error
        Run Keyword And Continue On Failure    Assert F
    END
    Run Keyword And Continue On Failure    Assert G

Deeply Nested Blocks
    [Tags]    robot:continue-on-failure
    FOR    ${index}    IN RANGE    3
        IF    $condition
            Run Keyword And Continue On Failure    Assert A
            ${result} =    Run Keyword And Continue On Failure    Get Value
        END
    END

Nested Blocks Without Tag
    FOR    ${index}    IN RANGE    3
        Run Keyword And Continue On Failure    Assert A
    END
