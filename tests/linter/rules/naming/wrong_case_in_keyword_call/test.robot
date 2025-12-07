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

Keyword(s) with words inside brackets
    Execute Command(s)
    Test Flash(es)
    Recognize Figure(s) (Math) From Picture
    Test Sulfur (S) Concentration

Keywords with plural suffixes
    Test Agile Story(-ies)
    Feed Wolf(-ves)
    Life(-ves) Count Should Be

Questionable Test
    Test Time Input (s)
    Recognize Figure(s) (art) From Picture

Templated test
    [Template]    lowercase
    Pass


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
    Should Pass
    Edit Group's Report Logo
    Take2 Is Capitalized
    Quoted "Strings" Are Fine Too
    Keyword_With_underscores

Keyword With Library Import
    SeleniumLibrary.Input Text    ${txt_welcome}    Hello
    Input Text    ${txt_welcome}    Hello

Keyword With API Abbreviation Should Pass
    Keyword With Number Ins1de 0r In Fr0nt
    I Will Love U 4 Ever

Keyword With Unicode And Non Latin
    Eäi Saa Peittää
    日本語
    _

More Embedded Variables
    Keyword With Embedded ${var} Variable
    Keyword With Embedded ${var.attr} Variable
    Keyword With Embedded ${var}['key'] Variable
    Keyword With Embedded ${var}['${var}'] Variable

Execute Command(s)
    No Operation
    Log  ${TEST_NAME}

Test Agile Story(-ies)
    No Operation

Test Flash(es)
    No Operation

Feed Wolf(-ves)
    No Operation

Life(-ves) Count Should Be
    No Operation

Test Time Input (s)
    No Operation

Recognize Figure(s) (art) From Picture
    No Operation

Recognize Figure(s) (Math) From Picture
    No Operation

Dot in name foo.bar
    No Operation
