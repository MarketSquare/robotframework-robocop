*** Settings ***
Documentation  doc
Default Tags    roBot:TEST


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
    [Tags]  tagORtag  tagorand  andsmth  with space or reserved  robot:no-dry-run  robot:my_tag
    ...     robot:continue-on-failure    robot:recursive-continue-on-failure
    Keyword

Another Keyword
    [Tags]  robot:skip  robot:skip-on-failure  robot:exclude  robot:exit

Variable In Tag
    [Tags]    robot:${dynamic_behaviour}
    Keyword

