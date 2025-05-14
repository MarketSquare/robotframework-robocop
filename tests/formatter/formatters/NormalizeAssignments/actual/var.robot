*** Test Cases ***
VAR
    VAR    ${variable} =  value
    VAR    ${variable} =   value
    VAR    ${variable} =    value=
    VAR    ${assign} =    first    separator==
    VAR    &{dict} =    key=value    key2=value  # comment
    VAR    ${variable}=   value  # fmt: off
