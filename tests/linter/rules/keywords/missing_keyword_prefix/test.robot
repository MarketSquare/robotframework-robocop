*** Settings ***
Library     libs/Library.py
Library     libs/Utils.py
Resource    resources/login.resource
Library     Collections

*** Test Cases ***
Missing Prefix
    Login    user
    Given Logout
    Append To List    ${list}    item
    Keyword With value Argument

Prefixed Calls
    login.Login    user
    Collections.Append To List    ${list}    item

Ignored Calls
    Log    message
    Local Keyword
    ${name} =    Set Variable    Login
    Run Keyword    ${name}
    Not Defined Anywhere    argument

Library Prefix
    Library.with_prefix
    Without Prefix
    Utils Kw
    Aliased Keyword

*** Keywords ***
Local Keyword
    Log    local
