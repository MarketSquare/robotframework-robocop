*** Test Cases ***
Short VAR
    VAR    ${variable}    value

Long VAR
    VAR    ${long_variable_name_that_fills_up_half_of_available_space}    long string value that overflows over available space

VAR with options
    VAR    ${long_variable_name_that_fills_up_half_of_available_space}    long string value that overflows over available space    separator=${SPACE}    scope=GLOBAL


*** Keywords ***
VAR with long separators
    VAR                             ${variable_name}                                                                        value

Split VAR
    VAR
    ...    ${variable}
    ...    value
    VAR    @{long_variable_name_that_fills_up_half_of_available_space}    long string value that overflows over available space
    ...    second value
    VAR    @{list_with_empty}
    ...
    ...    ${value}
    VAR    @{list_with_empty}    long string value that overflows over available space    long string value that overflows over available space
    ...
    ...    ${value}