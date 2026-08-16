*** Keywords ***
Keyword with undefined arg
    [Arguments]    ${foo}    ${bar}=${EMPTY}    ${baz}=123
    No Operation

Keyword with undefined arg multiline
    [Arguments]
    ...  ${foo}
    ...  ${bar}=123
    ...  ${baz}=${EMPTY}
    ...  ${lorum}=${ipsum}
    No Operation

Keyword with valid defined defaults
    [Arguments]    ${foo}=something}=    ${bar}=hello}=world    ${ba=z}= 123
    No Operation

Keyword with valid empty defaults
    [Arguments]    ${foo}=${EMPTY}    ${bar}=@{EMPTY}    ${ba=z}=&{EMPTY}
    No Operation

Keyword with multiple violations in one line
    [Arguments]    ${arg}=${EMPTY}    ${arg2}=${EMPTY}
    No Operation

Keyword with invalid syntax
    [Arguments]    ${arg
    No Operation

Keyword with invalid syntax including equal sign
    [Arguments]    ${arg=
    No Operation

Keyword with named-only arguments
    [Arguments]    @{}    ${bar}=${EMPTY}    ${foo}=${None}
    No Operation
