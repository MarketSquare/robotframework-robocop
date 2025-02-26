*** Test Cases ***
test
    Keyword

Rename Me
    No Operation

*** Keywords ***
New Shining Name
   Also Rename This

Rename Me 2
    No Operation

I Am Fine
    But I Am Not

Underscores Are Bad
    Looks Like Python
    library_with_underscore.Looks Like Python

Keyword With Unicode And Non Latin
    Eäi Saa Peittää
    日本語
    _
    __

Ignore ${var} Embedded
    Also Ignore ${variable}['key'] Syntax

Structures
    FOR  ${var}  IN  1  2  3
        IF  condition
            Keyword
        ELSE IF
            Keyword
        ELSE
            Keyword
        END
            Keyword
    END

Double Underscores
    No Operation

All Upper Case
    Connect To System ABC
    Create Product DFG

Underscores And. Dots
    Foo. BAR Baz A B C
    Foo Bar BAZ
