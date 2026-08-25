*** Settings ***
Library    LibraryKeywords.py
Library    Collections

*** Test Cases ***
Valid Calls
    Keyword With Arguments    1
    Keyword With Arguments    1    2
    Keyword Without Arguments
    Keyword With Varargs    1    2    3
    Keyword With Named Only    1    strict=yes
    Append To List    ${list}    value
    Log    message

Invalid Calls
    Keyword With Arguments
    Keyword With Arguments    1    2    3
    Keyword Without Arguments    unexpected
    Keyword With Named Only    1
    Append To List
