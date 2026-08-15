*** Keywords ***
Login
    [Arguments]    ${username}
    Log    ${username}

Logout
    Log    bye

Keyword With ${embedded} Argument
    Log    ${embedded}
