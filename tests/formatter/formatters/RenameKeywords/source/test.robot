*** Test Cases ***
test
    keyword

Rename Me
    No Operation

*** Keywords ***
rename Me
   Also rename this

Rename Me 2
    No Operation

I Am Fine
    but i am not

Underscores_are_bad
    looks_like_python
    library_with_underscore.looks_like_python

Keyword With Unicode And Non Latin
    Eäi Saa Peittää
    日本語
    _
    __

Ignore ${var} embedded
    Also Ignore ${variable}['key'] syntax

Structures
    FOR  ${var}  IN  1  2  3
        IF  condition
            keyword
        ELSE IF
            keyword
        ELSE
            keyword
        END
            keyword
    END

Double__underscores
    No Operation

All Upper Case
    Connect To System ABC
    Create Product DFG

Underscores and. dots
    Foo. BAR Baz A b C
    _Foo bar BAZ

Quoted "${values_and_words}"
    Values IN quotes "should REMAIN fully UNaffected"
    Values IN quotes 'should REMAIN fully UNaffected'
    'Even if whole keyword is quote'
    I'll need to test partial quotes
    And "${variables}" and "some other ${variables}" "shall work"
    And "nested quotation "should not be" considered " and single "
