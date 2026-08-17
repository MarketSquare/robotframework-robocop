*** Settings ***
Default Tags    robot:recursive-continue-on-failure


*** Test Cases ***
Default Tags make wrapper redundant
    Run Keyword And Continue On Failure    Test Keyword

Local tags override Default Tags
    [Tags]    own
    Run Keyword And Continue On Failure    Not Redundant
