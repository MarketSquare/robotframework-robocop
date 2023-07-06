*** Settings ***
# Use Sleep in Suite stuff later


*** Test Cases ***
Test with sleeps
    Log    Let's sleep for some time.
    Sleep    10s
    Log    It may not be enough, let's do it in loop.
    FOR    ${var}    IN RANGE    1    10
        Sleep    ${var}  # non-parsable time strings are ignored
    END
    IF    ${var} == 10
        Sleep
        ...    1 min
    END
    Sleep
