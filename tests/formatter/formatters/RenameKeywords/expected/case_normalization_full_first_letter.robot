*** Test Cases ***
test
    Keyword

Rename Me
    No operation

*** Keywords ***
Rename me
   Also rename this

Rename me 2
    No operation

I am fine
    But i am not

Underscores are bad
    Looks like python
    library_with_underscore.Looks like python

Keyword with unicode and non latin
    Eäi saa peittää
    日本語
    _
    __

Ignore ${var} embedded
    Also ignore ${variable}['key'] syntax

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

Double underscores
    No operation

All upper case
    Connect to system abc
    Create product dfg

Underscores and. dots
    Foo. bar baz a b c
    foo bar baz
