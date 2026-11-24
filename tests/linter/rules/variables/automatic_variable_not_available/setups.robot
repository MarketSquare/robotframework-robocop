*** Test Cases ***
Setup Does Not See Earlier Textual Body Assignment
    ${TEST STATUS} =    Set Variable    value
    [Setup]    Log    ${TEST STATUS}

Setup Binding Is Visible To Earlier Textual Body
    Log    ${KEYWORD STATUS}
    [Setup]    Set Local Variable    \${KEYWORD STATUS}    value
