*** Settings ***
Test Tags    robot:continue-on-failure


*** Test Cases ***
Inherits Test Tags
    Run Keyword And Continue On Failure    Assert A
    Assert B

Test Tags Are Not Overwritten
    [Tags]    other
    Run Keyword And Continue On Failure    Assert A
