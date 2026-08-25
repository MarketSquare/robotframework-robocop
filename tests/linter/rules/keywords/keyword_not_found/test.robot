*** Settings ***
Resource    resources/keywords.resource
Library     Collections
Test Setup    NONE

*** Test Cases ***
Defined Keywords
    Login
    Keyword With Some Argument
    Append To List    ${list}    item
    Log    message
    Local Keyword

Missing Keyword
    Logout

Keyword Built From Variable
    ${name}    Set Variable    Login
    Run Keyword    ${name}

Missing Keyword In Run Keyword
    Run Keyword If    ${True}    Not Defined Anywhere

*** Keywords ***
Local Keyword
    Log    message
