*** Test Cases ***
Test Tags make wrapper redundant
    Run Keyword And Continue On Failure    Test Keyword

Test Tags can be removed
    [Tags]    -robot:continue-on-*
    Run Keyword And Continue On Failure    Test Keyword


*** Keywords ***
Keyword Tags make wrapper redundant
    Run Keyword And Continue On Failure    Keyword Call

Keyword Tags can be removed
    [Tags]    -robot:recursive-continue-on-failure
    Run Keyword And Continue On Failure    Keyword Call


*** Settings ***
Test Tags       robot:continue-on-failure
Keyword Tags    robot:recursive-continue-on-failure
