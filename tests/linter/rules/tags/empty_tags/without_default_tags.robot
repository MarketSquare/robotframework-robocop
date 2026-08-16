*** Settings ***
Documentation  doc


*** Test Cases ***
Test With Empty Tags
    [Tags]
    Keyword Call

Test With Empty Tags And Comment
    [Tags]    # comment
    Keyword Call


*** Keywords ***
Keyword With Empty Tags
    [Tags]
    No Operation
