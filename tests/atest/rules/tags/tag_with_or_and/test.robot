*** Settings ***
Documentation  doc
Force Tags  tagORtag2  tagor
Default Tags  tagORtag2  tagor  tag${AND}


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  tagORtag2  tagor  tag${OR}  tagOR${var}
    Pass
    Keyword
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    ...              Tags:  tagORtag2,  tagor, tag${OR}
    No Operation
    Pass
    No Operation
    Fail
