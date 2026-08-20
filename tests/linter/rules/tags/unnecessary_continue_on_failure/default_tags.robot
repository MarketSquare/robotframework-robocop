*** Settings ***
Default Tags    robot:continue-on-failure


*** Test Cases ***
Inherits Default Tags
    Run Keyword And Continue On Failure    Assert A

Overwrites Default Tags
    [Tags]    other
    Run Keyword And Continue On Failure    Assert A
