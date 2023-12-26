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
Test Lowercase Settings
    [documentation]  doc
    [tags]  sometag
    [setup]  Keyword
    [template]  template
    [timeout]  timeout
    Pass
    Keyword
    One More
    [teardown]  Keyword

Test Titlecase Settings
    [Documentation]  doc
    [Tags]  sometag
    [Setup]  Keyword
    [Template]  template
    [Timeout]  timeout
    Pass
    Keyword
    One More
    [Teardown]  Keyword

Test Uppercase Settings
    [DOCUMENTATION]  doc
    [TAGS]  sometag
    [SETUP]  Keyword
    [TEMPLATE]  template
    [TIMEOUT]  timeout
    Pass
    Keyword
    One More
    [TEARDOWN]  Keyword


*** Keywords ***
Keyword Lowercase Settings
    [documentation]  this is doc
    [tags]  sometag
    [arguments]  arg1  arg2
    [timeout]  timeout
    No Operation
    Pass
    No Operation
    Fail
    [teardown]  Teardown
    [return]  value

Keyword Titlecase Settings
    [Documentation]  this is doc
    [Tags]  sometag
    [Arguments]  arg1  arg2
    [Timeout]  timeout
    No Operation
    Pass
    No Operation
    Fail
    [Teardown]  Teardown
    [Return]  value

Keyword Uppercase Settings
    [DOCUMENTATION]  this is doc
    [TAGS]  sometag
    [ARGUMENTS]  arg1  arg2
    [TIMEOUT]  timeout
    No Operation
    Pass
    No Operation
    Fail
    [TEARDOWN]  Teardown
    [RETURN]  value

New Return
    RETURN
