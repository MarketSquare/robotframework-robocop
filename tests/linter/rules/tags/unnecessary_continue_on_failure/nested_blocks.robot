*** Test Cases ***
Nested Blocks
    [Tags]    robot:continue-on-failure
    FOR    ${index}    IN RANGE    3
        Run Keyword And Continue On Failure    Assert A
    END
    IF    $condition
        Run Keyword And Continue On Failure    Assert B
    END
    Run Keyword And Continue On Failure    Assert C
