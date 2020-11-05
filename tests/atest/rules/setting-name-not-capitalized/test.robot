*** Settings ***
Documentation   doc
library         Library
resource        resource.robot
variablES       variables.py
suite setup     Keyword
suite Teardown  Keyword
test seTup      Keyword
Test teardown   Keyword
force tags      tag
default tags    defaulttag


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    [setup]  Keyword
    Pass
    Keyword
    One More
    [teardown]  Keyword


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail
