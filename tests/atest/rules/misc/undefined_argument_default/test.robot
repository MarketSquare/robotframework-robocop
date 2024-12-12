*** Keywords ***
Keyword with undefined arg
    [Arguments]    ${foo}    ${bar}=    ${baz}=123
    No Operation

Keyword with undefined arg multiline
    [Arguments]
    ...  ${foo}
    ...  ${bar}=123
    ...  ${baz}=
    No Operation

Keyword with valid defined defaults
    [Arguments]    ${foo}=something}=    ${bar}=hello}=world    ${ba=z}= 123
    No Operation


Keyword with valid empty defaults
    [Arguments]    ${foo}=${EMPTY}    ${bar}=@{EMPTY}    ${ba=z}=&{EMPTY}
    No Operation
