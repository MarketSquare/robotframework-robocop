# robocop: disable=too-few-calls-in-keyword,0302
*** Settings ***
Documentation  This is suite doc

*** Test Cases ***
This is test
    [Documentation]  Test case doc
    ${arg1}  This Is Keyword

*** Keywords ***
This Is Keyword
    [Documentation]  Keyword doc
    [Return]

This Is Keyword2
    [Documentation]  Keyword doc
    [Return]  ${arg}

This Is Keyword3
    [Documentation]  Keyword doc
    [Return]  ${arg}  ${arg}  ${arg}  ${arg}  ${arg}

This Is Keyword4
    [Documentation]  Keyword doc
    Return From Keyword

This Is Keyword5
    [Documentation]  Keyword doc
    Return From Keyword  ${arg}  ${arg}

This Is Keyword6
    [Documentation]  Keyword doc
    Return From Keyword  ${arg}  ${arg}  ${arg}  ${arg}  ${arg}

This Is Keyword4
    [Documentation]  Keyword doc
    Return From Keyword If  ${True}

This Is Keyword5
    [Documentation]  Keyword doc
    Return From Keyword If  ${True}  ${arg}  ${arg}

This Is Keyword6
    [Documentation]  Keyword doc
    FOR  ${elem}  IN  smth  smth
        Return From Keyword If  ${True}  ${arg}  ${arg}  ${arg}  ${arg}  ${arg}
    END