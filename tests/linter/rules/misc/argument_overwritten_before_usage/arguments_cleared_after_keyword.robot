*** Variables ***
${VARIABLE}    value


*** Keywords ***
Not used argument
    [Arguments]    ${name}
    No Operation


*** Test Cases ***
Test with variable using the same name as previous keyword argument
    ${name}    Keyword Call
