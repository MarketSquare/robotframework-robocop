*** Test Cases ***
All Calls Wrapped
    Run Keyword And Continue On Failure    Assert A
    Run Keyword And Continue On Failure    Assert B

Single Call
    Run Keyword And Continue On Failure    Assert A

Mixed Calls
    Run Keyword And Continue On Failure    Assert A
    Run Keyword And Continue On Failure    Assert B
    Assert C

With Settings
    [Documentation]    Settings are not keyword calls.
    [Setup]    Setup Keyword
    Run Keyword And Continue On Failure    Assert A
    Run Keyword And Continue On Failure    Assert B
    [Teardown]    Teardown Keyword

Already Tagged
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    Assert A
    Run Keyword And Continue On Failure    Assert B

With For Loop
    Run Keyword And Continue On Failure    Assert A
    FOR    ${index}    IN RANGE    3
        Run Keyword And Continue On Failure    Assert B
    END

With Not Wrapped Call In For Loop
    Run Keyword And Continue On Failure    Assert A
    FOR    ${index}    IN RANGE    3
        Assert B
    END

With Assignment
    Run Keyword And Continue On Failure    Assert A
    ${result} =    Run Keyword And Continue On Failure    Get Value
