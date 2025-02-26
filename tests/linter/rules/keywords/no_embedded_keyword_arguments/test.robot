*** Keywords ***
Keyword without any arguments
    No Operation

Keyword with normal arguments
    [Arguments]    ${foo}    ${bar}    ${baz}=123
    No Operation

Keyword with ${one} embedded argument
    No Operation

Keyword with ${count} embedded ${arguments}
    No Operation

${keyword} ${with} ${only} ${embedded} ${arguments}
    No Operation

Keyword with both ${embedded} and normal arguments
    [Arguments]    ${foo}
    No Operation

Keyword with embedded ${regex:(\d{4}-\d{2}-\d{2}|today)} argument
    No Operation
