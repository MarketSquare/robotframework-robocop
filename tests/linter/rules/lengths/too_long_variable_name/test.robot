*** Settings ***
Documentation       Lines that should be reported by too-long-variable-names have a comment with the expected length


*** Variables ***
${SHORT_SUITE_VARIABLE_NAME}                        value
${SUITE_VARIABLE_NAME_THAT_IS_WAY_TOOO_LONG}        value    # 41
@{SUITE_VARIABLE_NAME_FOR_LIST_THAT_IS_TOO_LONG}    item1    item2    # 45
&{SUITE_VARIABLE_NAME_FOR_DICT_THAT_IS_TOO_LONG}    key=value    # 45


*** Test Cases ***
Test
    ${short_variable_name}    Set Variable    value
    ${variable_name_fits_exactly_into_max_len_}    Set Variable    value    # Not reported
    ${local_variable_name_that_is_way_tooo_long}    Set Variable    value    # 41
    ${different_local_variable_name_that_is_too_long}    Set Variable    value    # 46

    ${different_short_variable_name}    ${another_local_variable_name_that_is_too_long}    Set Variable    value    # 44

    # Variable names are judged by length of visual apperance, not evaluated/escaped length
    ${yet another local variable name that is too long}    Set Variable    value    # 48
    ${a\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ b}    Set Variable    value    # 42

    # item access by extended syntax
    &{local_dict_var_just_shy_of_max_len_a} =    Create Dictionary    first_name=unknown
    ${local_dict_var_just_shy_of_max_len_c.first_name}    Set Variable         John
    &{local_dict_variable_name_that_is_too_long_a}    Set Variable    ${existing_dict}    # 43
    ${local_dict_variable_name_that_is_too_long_c.last_name}    Set Variable         Doe    # 43
    ${local_dict_var_just_shy_of_max_len_d\.last_name}    Set Variable         Doe

Test Variants
    Set Local Variable    ${short_local_variable_name}    value
    Set Local Variable    ${local_variable_name_that_is_way_tooo_long}    value    # 41
    Set Suite Variable    ${DIFFERENT_SUITE_VARIABLE_NAME_THAT_IS_WAY_TOOO_LONG}    value    # 51
    Set Test Variable    ${TEST_VARIABLE_NAME_THAT_IS_WAY_TOOOO_LONG}    value    # 41
    Set Task Variable    ${TASK_VARIABLE_NAME_THAT_IS_WAY_TOOOO_LONG}    value    # 41
    Set Global Variable    ${GLOBAL_VARIABLE_NAME_THAT_IS_WAY_TOO_LONG}    value    # 41

    # Usign recommended formats
    Set Task Variable    $different_task_variable_name_that_is_too_long    value    # 45
    Set Global Variable    \${different_global_variable_name_that_is_too_long}    value    # 47

    # Reassigning existing variables already used in current scope
    ${local_variable_name_that_is_way_tooo_long}    Set Variable    value
    ${different_local_variable_name_that_is_too_long}    Set Variable    value    # 46
    Set Local Variable    ${different_local_variable_name_that_is_too_long}    value
    Set Test Variable    ${TEST_VARIABLE_NAME_THAT_IS_WAY_TOOOO_LONG}    value

    # Reassigning existing variables outside of current scope; Will be re-reported
    Set Suite Variable    ${SHORT_SUITE_VARIABLE_NAME}    value
    Set Suite Variable    ${SUITE_VARIABLE_NAME_THAT_IS_WAY_TOOO_LONG}    value    # 41

    ${short_local_variable_name}    ${task_variable_name_that_is_way_toooo_long}    Some Keyword

    # Reassign usign recommended formats
    ${another_local_variable_name_that_is_too_long}    Set Variable    value    # 44
    Set Local Variable    $another_local_variable_name_that_is_too_long    value
    Set Suite Variable    \${SUITE_VARIABLE_NAME_THAT_IS_WAY_TOOO_LONG}    value    # 41
    Set Local Variable    @{local_list_variable_name_that_is_too_long}    @{EMPTY}    # 41
    Set Local Variable    \@different_local_list_variable_name_that_is_too_long    @{EMPTY}    # 51
    Set Local Variable    @another_local_list_variable_name_that_is_too_long    @{EMPTY}    # 49
    Set Local Variable    &{local_dict_variable_name_that_is_too_long}    &{EMPTY}    # 41
    Set Local Variable    \&{different_local_dict_variable_name_that_is_too_long}    &{EMPTY}    # 51
    Set Local Variable    &another_local_dict_variable_name_that_is_too_long    &{EMPTY}    # 49

Test Return Values
    ${short_variable_name}    Set Variable    value
    ${variable_set_from_return_that_is_too_long}    Set Variable    value    # 41
    ${different_short_variable_name}    ${different_variable_set_from_return_that_is_too_long} =    Some Keyword    # 51

    # Reassigning existing variables
    ${different_short_variable_name}    ${different_variable_set_from_return_that_is_too_long}    Some Keyword

Test For
    FOR    ${short_iteration_variable_name}    IN RANGE    ${10}
        # Making sure that body is visited:
        ${local_variable_name_that_is_way_tooo_long}    Set Variable    value    # 41
    END

    FOR    ${iteration_variable_name_that_is_way_too_long}    IN    apple    banana    # 44
        None Shall Pass    ${None}
    END

    FOR    ${another_short_iteration_variable_name}    ${different_iteration_variable_that_is_too_long}    IN ENUMERATE    @{list}    # 45
        FOR    ${another_iteration_variable_that_is_too_long}    ${yet_another_iteration_variable_that_is_too_long}    IN ZIP    @{list}    @{list}    # 43, 47
            Comment    Even nested for loops are checked
        END
    END
    
    # Reusing existing variable; Not reported because variable in still in same scope
    FOR    ${iteration_variable_name_that_is_way_too_long}    IN    apple    banana
        No Operation
    END


*** Keywords ***
Some Keyword
    [Arguments]
    ...    ${short_argument_name}
    ...    ${keyword_argument_name_that_is_way_too_long}    # 42
    ...    ${short_argument_name_with_default_value}=default
    ...    ${keyword_argument_just_shy_of_max_len:invalid}=default    # 44
    # Making sure that body is visited and scope works
    ${local_variable_name_that_is_way_tooo_long}    Set Variable    value    # 41
    ${keyword_argument_name_that_is_way_too_long}    Set Variable    value

Keyword With ${short_embedded_argument_name} And ${embedded_argument_name_that_is_way_too_long} To Do Something With    # 43
    [Arguments]    ${short_argument_name}=${None}    ${argument_name_with_default_value_that_it_too_long}=default    # 49
    Comment    Even keywords with embedded arguments can have additional arguments
    &{local_dict_variable_name_that_is_too_long}    Set Variable    ${existing_dict}    # 41

Keyword ${embedded_just_shy_of_max_len_contains:pattern} And ${embedded_name_that_is_too_long_that_contains:pattern}    # 44
    Log    ${embedded_just_shy_of_max_len_contains}

