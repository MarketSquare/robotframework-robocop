*** Test Cases ***
Recursive Tag
    [Tags]    robot:recursive-continue-on-failure
    Run Keyword And Continue On Failure    Assert A
    BuiltIn.Run Keyword And Continue On Failure    Assert B

Normalized Tag
    [Tags]    ROBOT:Continue-On-Failure
    Run Keyword And Continue On Failure    Assert A

Bdd Prefix
    [Tags]    robot:continue-on-failure
    Given Run Keyword And Continue On Failure    Assert A

Assigned Call
    [Tags]    robot:continue-on-failure
    ${result} =    Run Keyword And Continue On Failure    Get Value

Without Tag
    Run Keyword And Continue On Failure    Assert A
