*** Settings ***
Library    Collections
Library    OperatingSystem
Library    String    AS    Str
Library    NotExisting
Resource    resources/keywords.resource

*** Test Cases ***
Test
    Append To List    ${list}    item
    Str.Convert To Upper Case    text
    Keyword From Resource
