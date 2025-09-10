*** Settings ***
Documentation       Test variable creation with VAR syntax and dynamic variable names (both added in 7.0). Item access moved here, because it was only added in 6.1


*** Variables ***
${SHORT_SUITE_VARIABLE_NAME}                                            name
${SUITE_VARIABLE_NAME_THAT_IS_WAY_TOOO_LONG}        value    # 41
${SUITE_VARIABLE_NAME_THAT_CONTAINS_${SHORT_SUITE_VARIABLE_NAME}}       value    # 62


*** Test Cases ***
Test
    VAR    ${short_variable_name}    value
    VAR    ${loong_but_still_acceptable_variable_name}    value

    # Currently re-reported because 'scope' is not respected
    VAR    ${SUITE_VARIABLE_NAME_THAT_IS_WAY_TOOO_LONG}    value    scope=SUITE    # 41
    VAR    ${SETTING_GLOBAL_VARIABLE_WITH_TOO_LONG_NAME}    value    scope=GLOBAL    # 42

Test Dynamic Names
    ${a${SPACE}${SPACE}${SPACE}${SPACE}${SPACE}b}    Set Variable    value    # 42
    ${short_variable_name}    Set Variable    name
    ${local_variable_name_that_contains_dyn_${short_variable_name}}    Set Variable    value    # 60

    # Usage of literal name of existing variable; Will be reported again with new length
    ${local_variable_name_that_contains_dyn_name}    Set Variable    value    # 42

    # Some extended variable sytnax
    VAR    ${another_var_name_${short_variable_name}}    value
    VAR    ${different_var_${short_variable_name*2}}    value
    VAR    ${other_var_${short_variable_name.key_name}}   value    # 41

    #Using recommended syntax
    Set Test Variable    ${TEST_VARIABLE_NAME_THAT_CONTAINS_DYN_${short_variable_name}}    value    # 59
    Set Task Variable    \${TASK_VARIABLE_NAME_THAT_CONTAINS_DYN_${short_variable_name}}    value    # 59
    Set Suite Variable    $SUITE_VARIABLE_NAME_THAT_CONTAINS_DYN_${short_variable_name}    value    # 60
    Set Local Variable    $variable_name_with_${var_a}_and_${var_b}    value
    Set Local Variable    $long_variable_name_with_@{var_a}[0]_and_${var_b}    value    # 48

    ${another_variable_name_with_@{var_a}[0]_and_${var_b}}    Keyword    # 51
    
Test Item Access
    Comment    Added in RF 6.1
    # list variables and item access; Accessing items of existing list should not be reported
    ${local_list_name_just_shy_of_max_len_a}[${1}]    Set Variable    second
    ${local_list_name_just_shy_of_max_len_b}[2:3] =     Create List      third
    ${local_list_variable_name_that_is_too_long}[0]    Set Variable    first    # 41

    # items access shouldn't count towards length
    ${local_dict_var_just_shy_of_max_len_b}[first_name] =    Set Variable         John
    ${local_dict_variable_name_that_is_too_long_b}[last_name][0] =     Set Variable         Doe    # 43

*** Keywords ***
Something
    # Currently re-reported because 'scope' is not evaluated
    VAR    ${SETTING_GLOBAL_VARIABLE_WITH_TOO_LONG_NAME}    value    scope=GLOBAL    # 42
