*** Settings ***
Resource    resources/first.resource
Resource    resources/second.resource
Library    Collections

*** Test Cases ***
Ambiguous Call
    Login    user    password

Not Ambiguous When Prefixed
    first.Login    user    password

Not Ambiguous When Defined In Single Resource
    Only In First
    Only In Second

Not Ambiguous When Name Is Built From Variable
    ${name}    Set Variable    Login
    Run Keyword    ${name}

Resource Keyword Wins Over Library
    Append To List    ${list}    item

Keyword From The File Wins
    Defined In File And Resource

*** Keywords ***
Defined In File And Resource
    Log    keyword from the file itself
