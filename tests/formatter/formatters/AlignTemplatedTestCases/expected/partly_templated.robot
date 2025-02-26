*** Settings ***
Test Template       Test Commit Message


*** Test Cases ***                  UNLINTED FILE               LINTED FILE
Misplaced Git Trailer               misplaced_trailer.txt       misplaced_trailer_linted.txt
Mixed Unordered List Symbols        mixed_unordered.txt         mixed_unordered_linted.txt
Incorrectly Ordered List            ordered.txt                 ordered_linted.txt
Unaligned List Item Indention       unaligned.txt               unaligned_linted.txt
Garbage Commit Message              garbage.txt                 garbage_linted.txt
Valid Commit Message                unchanged.txt               unchanged_linted.txt            ${type trailer}     ${type trailer}\n${trailer block}
Header Validation
    [Template]    NONE
    ${valid header} =    Validate Header    ${header}
    Should Be True    ${valid header}
    ${err invalid header} =    Validate Header    ${EMPTY}
    Should Not Be True    ${err invalid header}
Trailer Validation
    [Template]
    ${valid type trailer} =    Validate Type Trailer    ${type trailer}
    Should Be True    ${valid type trailer}
    ${err invalid trailer} =    Validate Type Trailer    ${EMPTY}
    Should Not Be True    ${err invalid trailer}
