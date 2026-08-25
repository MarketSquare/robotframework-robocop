*** Settings ***
Keyword Tags    robot:continue-on-failure


*** Keywords ***
Keyword With Suite Tag
    Run Keyword And Continue On Failure    Assert A

Keyword With Local Tag
    [Tags]    robot:continue-on-failure
    Run Keyword And Continue On Failure    Assert A
