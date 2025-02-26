*** Settings ***
Documentation  docs


*** Test Cases ***
Test
    [Tags]  sometag
    Pass
    Keyword
    One More

Test 2
    [Tags]  othertag  sometag
    Pass
    Keyword
    One More
