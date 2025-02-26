*** Test Cases ***
Short VAR
    ${variable}    Set Variable    value

Long VAR
    ${long_variable_name_that_fills_up_half_of_available_space}    Set Variable    long string value that overflows over available space

VAR with options
    Set Global Variable    ${long_variable_name_that_fills_up_half_of_available_space}    long string value that overflows over available space    separator=${SPACE}


*** Keywords ***
VAR with long separators
    ${variable_name}                Set Variable                                                                                                     value

Split VAR
    ${variable}    Set Variable
    ...    value
    @{long_variable_name_that_fills_up_half_of_available_space}    Create List        long string value that overflows over available space
    ...    second value
    @{list_with_empty}    Create List
    ...
    ...    ${value}
    @{list_with_empty}    Create List     long string value that overflows over available space    long string value that overflows over available space
    ...
    ...    ${value}
