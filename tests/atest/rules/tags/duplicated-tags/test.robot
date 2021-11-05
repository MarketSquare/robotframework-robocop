*** Settings ***
Documentation  doc
Default Tags  tag  othertag  Tag
Force Tags  t ag  tag  sometag

*** Test Cases ***
Test With Tags
    [Tags]    dummy  tag  TAG
    Log    2


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail

Keyword With Tags
    [Tags]    tag  sometag    taG   t-ag

Keyword With Tags In Documentation
    [Documentation]  Tags:  tag,  sometag,  tag,  t ag

Keyword With Empty Tags
    [Tags]
    No Operation
