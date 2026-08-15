*** Settings ***
Test Template    Template Keyword


*** Test Cases ***
Test with empty template
    [Template]
    Keyword Call

Test with explicit NONE
    [Template]    NONE
    Keyword Call
