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
