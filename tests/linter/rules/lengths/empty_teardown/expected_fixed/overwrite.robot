*** Settings ***
Test Teardown    Teardown Keyword


*** Test Cases ***
Test with empty teardown
    [Teardown]    NONE
    Keyword Call

Test with explicit NONE
    [Teardown]    NONE
    Keyword Call


*** Keywords ***
Keyword with empty teardown
    No Operation
