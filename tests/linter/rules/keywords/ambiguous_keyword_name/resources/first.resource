*** Keywords ***
Login
    Log    login from first resource

Only In First
    Log    message

Defined In File And Resource
    Log    message

Append To List
    [Arguments]    ${list}    ${item}
    Log    keyword with the same name as a library keyword
