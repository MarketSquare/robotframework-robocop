*** Settings ***
Test Setup    Setup Keyword


*** Test Cases ***
Test with empty setup
    [Setup]    NONE
    Keyword Call

Test with explicit NONE
    [Setup]    NONE
    Keyword Call
