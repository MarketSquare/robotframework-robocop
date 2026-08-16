*** Settings ***
Test Timeout    1 min


*** Test Cases ***
Test with empty timeout
    [Timeout]    NONE
    Keyword Call

Test with explicit NONE
    [Timeout]    NONE
    Keyword Call


*** Keywords ***
Keyword with empty timeout
    No Operation
