*** Settings ***
Documentation  doc
Suite Setup  keyword
Suite Teardown  keyword
Test Setup  keyword
Test Teardown  keyword



*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    [Setup]  keyword
    pass
    Keyword
    One More
    [Teardown]  keyword


*** Keywords ***
keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    FOR  ${var}  IN RANGE  10
    /  Log  ${var}
    Fail

 # special case

Keyword With ${var} Variable
    Should Pass

Keyword-With_Special $ Chars 10
    Should Pass

Keyword With Library Import
    SeleniumLibrary.Input Text    ${txt_welcome}    Hello
    Input Text    ${txt_welcome}    Hello
