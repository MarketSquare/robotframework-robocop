*** Settings ***
Documentation  Redundant equal signs


*** Test Cases ***
Test
    ${var}=  Keyword
    ${var} =  Keyword

*** Keywords ***
Keyword
    ${var}=  Keyword
    ${var} =  Keyword