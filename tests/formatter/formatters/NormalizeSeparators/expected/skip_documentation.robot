# this is    comment

*** Settings ***
Library    library.py    WITH NAME    alias

Force Tags    tag
...    tag

Documentation  doc
...      multi
...  line

*** Variables ***
${var}    3
 ${var2}    4

*** Test Cases ***
Test case
    [Setup]    Keyword
    [Documentation]  First word   Second word
    Keyword    with    arg
    ...    and    multi    lines
    [Teardown]    Keyword

Test case with structures
    FOR    ${variable}    IN    1    2
        Keyword
        IF    ${condition}
            Log    ${stuff}    console=True
        END
    END

*** Keywords ***
Keyword
Another Keyword
    [Arguments]    ${arg}
    [Documentation]  First word   Second word
    ...  Third.
    Should Be Equal    1
    ...    ${arg}
    IF    ${condition}
        FOR    ${v}    IN RANGE    10
            Keyword
        END
    END

Keyword With Tabulators
    Keyword
    ...    2
    ...    ${arg}
