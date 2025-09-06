*** Settings ******
Documentation    This test file contains various invalid variable names to test the linter rule for too long variable names.

*** Variables ***
SUITE_VARIABLE_JUST_LIKE_THIS    value
${NOT_CLOSED_SUITE_VARIABLE    value
  ${WITH_SPACES_BEFORE}    value
${TOO_LONG_SUITE_VARIABLE_NAME_THAT_IS_NOT_CLOSED
${ANOTHER_TOO_LONG_SUITE_VARIABLE_NAME=Some Value

*** Test Cases ***
Test
    ${short_variable_name}    Set Variable    value
    ${local_variable_name_that_is_way_tooo_long}    Set Variable    value    # 41
    ${different_local_variable_name_that_is_too_long    Set Variable    value

    # Variable names are judged by length of visual apperance, not evaluated/escaped length
    $yet another local variable name that is too long    Set Variable    value
    ${a\ \ \ \ \ \ \ \ \ \ \  \ \ \ \ \ \ \ \ b}    Set Variable    value

    # list variables and item access; Accessing items of existing list should not be reported
    ${local_list_name_just_shy_of_max_len_a}[$1}]    Set Variable    second
    ${local_list_name_just_shy_of_max_len_b}2:3] =     Create List      third
    ${local_list_variable_name_that_is_too_long}[0    Set Variable    first

    # dict variables and item access; items access shouldn't count towards length
    {local_dict_var_just_shy_of_max_len_a} =    Create Dictionary    first_name=unknown
    ${local_dict_var_just_shy_of_max_len_b.first_name] =    Set Variable         John
    local_dict_var_just_shy_of_max_len_c.first_name    Set Variable         John
    ${local_dict_variable_name_that_is_too_long_b}[last_name[0] =     Set Variable         Doe


Test Variants
    Set Local Variable    ${short_local_variable_name}    value
    Set Local Variable    local_variable_name_that_is_way_tooo_long    value
    Set Suite Variable    ${DIFFERENT_SUITE_VARIABLE_NAME_THAT_IS_WAY_TOOO_LONG    value
    Set Test Variable    {TEST_VARIABLE_NAME_THAT_IS_WAY_TOOOO_LONG}    value

Test For
    FOR    ${short_iteration_variable_name    IN RANGE    ${10}
        # Making sure that body is visited:
        ${local_variable_name_that_is_way_tooo_long}    Set Variable    value    # 41
    END

    FOR    $iteration_variable_name_that_is_way_too_long    IN    apple    banana
        None Shall Pass    ${None}
    END

    FOR    another_short_iteration_variable_name    $different_iteration_variable_that_is_too_long}    IN ENUMERATE    @{list}
        FOR    \${another_iteration_variable_that_is_too_long}    ${yet_another_iteration_variable_that_is_too_long}    IN ZIP    @{list}    @{list}
            Comment    Even nested for loops are checked
        END
    END
    
    FOR    ${iteration_variable_name_that_is_way_too_long}    IN    apple    banana    # 44
        No Operation
    END

*** Keywords ***
Valid Keyword
    [Arguments]    ${arg1}    ${arg2}
    No Operation

Invalid Keyword Argument
    [Arguments]    ${arg1    ${inbetween_argument_with_too_long_arg_name}    $arg3}    $arg4    \arg5    # 41
    Commnent    Checking continues with remaining arguments after invalid argument

Invalid Keyword Arguments With Default Values
    [Arguments]    ${arg1=value    ${inbetween_argument_with_too_long_arg_name}=value    $args3}=value    # 41
    No Operation

Keyword With ${{short_embedded_argument_name} And ${embedded_argument_name_that_is_way_too_long}} To Do Something With    # 81
    [Arguments]    ${short_argument_name=${None}    $another_short_argument_name}=default
    Comment    Even keywords with embedded arguments can have additional arguments
    &{local_dict_variable_name_that_is_too_long}    Set Variable    ${existing_dict}    # 41

Keyword ${embedded_arg_with_invalid_pattern_setting:pattern:pattern}    # 41; everything after first ':' is ignored
    No Operation
