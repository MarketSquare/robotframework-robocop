*** Test Cases ***
test
    Keyword  # robocop: fmt: off

Rename Me
    No Operation

*** Keywords ***
Rename Me  # robocop: fmt: off
   Also Rename This  # robocop: fmt: off

Rename Me 2
    No Operation
# robocop: fmt: off
I Am Fine
    But I Am Not
# robocop: fmt: on
Underscores Are Bad  # robocop: fmt: off
    Looks Like Python  # robocop: fmt: off
    library_with_underscore.Looks Like Python  # robocop: fmt: off

Keyword With Unicode And Non Latin
    Eäi Saa Peittää
    日本語
    _
    __
# robocop: fmt: off
Ignore ${var} Embedded
    Also Ignore ${variable}['key'] Syntax
# robocop: fmt: on
Structures
    FOR  ${var}  IN  1  2  3
        # robocop: fmt: off
        IF  condition
            Keyword
        ELSE IF
            Keyword
        ELSE
            Keyword
        END
            Keyword
    END
# robocop: fmt: off
Double Underscores
    No Operation

All Upper Case
    Connect To System ABC
    Create Product DFG
