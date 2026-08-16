*** Settings ***
Documentation   doc
Library         Library
Resource        resource.robot
Variables       variables.py
Suite Setup     Keyword
Suite Teardown  Keyword
Test Setup      Keyword
Test Teardown   Keyword
Force Tags      tag
Default Tags    defaulttag


*** Test Cases ***
Test Lowercase Settings
    [Documentation]  doc
    [Tags]  sometag
    [Setup]  Keyword
    [Template]  template
    [Timeout]  timeout
    Pass
    Keyword
    One More
    [Teardown]  Keyword

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
