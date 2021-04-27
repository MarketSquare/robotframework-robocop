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

Keyword With Embedded ${var} Variable
    Should Pass

Keyword With Embedded @{list} Variable
    Should Pass

Keyword With Embedded &{dict} Variable
    Should Pass

Keyword-With_Special $ Chars 10
    Should pass
    Edit group's report logo
    Take2 Is Capitalized
    Quoted "Strings" Are Fine Too
    Keyword_With_underscores

Keyword With Library Import
    SeleniumLibrary.Input text    ${txt_welcome}    Hello
    Input text    ${txt_welcome}    Hello

Keyword With API Abbreviation Should Pass
    Keyword with number ins1de or in fr0nt
    I will love u 4 ever

Keyword With Unicode And Non Latin
    Eäi saa peittää
    日本語
    _