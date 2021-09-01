*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail

Keyword With Reserved Tags
    [Documentation]  Tags:  tagORtag,  tagorand,  andsmth,  with space or reserved,  robot:no-dry-run,  robot:my_tag    robot:continue-on-failure    robot:recursive-continue-on-failure
