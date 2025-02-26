*** Test Cases ***
test
    keyword  # robotidy: off

Rename Me
    No Operation

*** Keywords ***
rename Me  # robotidy: off
   Also rename this  # robotidy: off

Rename Me 2
    No Operation
# robotidy: off
I Am Fine
    but i am not
# robotidy: on
Underscores_are_bad  # robotidy: off
    looks_like_python  # robotidy: off
    library_with_underscore.looks_like_python  # robotidy: off

Keyword With Unicode And Non Latin
    Eäi Saa Peittää
    日本語
    _
    __
# robotidy: off
Ignore ${var} embedded
    Also Ignore ${variable}['key'] syntax
# robotidy: on
Structures
    FOR  ${var}  IN  1  2  3
        # robotidy: off
        IF  condition
            keyword
        ELSE IF
            keyword
        ELSE
            keyword
        END
            keyword
    END
# robotidy: off
Double__underscores
    No Operation

All Upper Case
    Connect To System ABC
    Create Product DFG
