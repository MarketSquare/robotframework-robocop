*** Keywords ***
Keyword
    [Arguments]   ${argument_name}
    [Tags]    tag    tag
    Log    ${argument_name}
    Perform Action And Wait    ${argument_name}
