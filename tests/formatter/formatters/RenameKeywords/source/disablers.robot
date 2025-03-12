*** Test Cases ***
test
    keyword  # robocop: fmt: off

Rename Me
    No Operation

*** Keywords ***
rename Me  # robocop: fmt: off
   Also rename this  # robocop: fmt: off

Rename Me 2
    No Operation
# robocop: fmt: off
I Am Fine
    but i am not
# robocop: fmt: on
Underscores_are_bad  # robocop: fmt: off
    looks_like_python  # robocop: fmt: off
    library_with_underscore.looks_like_python  # robocop: fmt: off

Keyword With Unicode And Non Latin
    Eäi Saa Peittää
    日本語
    _
    __
# robocop: fmt: off
Ignore ${var} embedded
    Also Ignore ${variable}['key'] syntax
# robocop: fmt: on
Structures
    FOR  ${var}  IN  1  2  3
        # robocop: fmt: off
        IF  condition
            keyword
        ELSE IF
            keyword
        ELSE
            keyword
        END
            keyword
    END
# robocop: fmt: off
Double__underscores
    No Operation

All Upper Case
    Connect To System ABC
    Create Product DFG
