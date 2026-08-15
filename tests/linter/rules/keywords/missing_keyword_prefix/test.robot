*** Settings ***
Resource    resources/login.resource
Library     Collections
Library     String    AS    Str

*** Test Cases ***
Missing Prefix
    Login    user
    Given Logout
    Append To List    ${list}    item
    Convert To Lower Case    ABC
    Keyword With value Argument

Prefixed Calls
    login.Login    user
    Collections.Append To List    ${list}    item
    Str.Convert To Lower Case    ABC

Ignored Calls
    Log    message
    Local Keyword
    ${name} =    Set Variable    Login
    Run Keyword    ${name}
    Not Defined Anywhere    argument

*** Keywords ***
Local Keyword
    Log    local
