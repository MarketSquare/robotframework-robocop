*** Settings ***
Force Tags   tag
...  other tag

...  also tag

*** Test Cases ***
Test
    Keyword With
    ...  Multiline arguments

    ...  With empty lines


    ...   Which should be removed

*** Keywords ***
Multiline assignments
    ${argument}
    ...    ${argument}

    ...    Keyword

    ...    ${value}

Header
    [Setup]    Keyword

    ...    ${arg}
    FOR    ${var}  IN    ${val}
    ...  5

    ...  6
        Keyword
    END
