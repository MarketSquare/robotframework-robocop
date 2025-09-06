*** Settings ***
Documentation       doc


*** Test Cases ***
Test
    TRY
        # Making sure that try branch is visited:
        ${local_variable_name_that_is_way_tooo_long}    Set Variable    value    # 41
    EXCEPT    *warn*    AS    ${short_name}
        No Operation
    EXCEPT    *err*    AS    ${still_acceptable_name_for_captured_error}
        # Making sure that except branch is visited:
        ${different_short_variable_name}    ${another_local_variable_name_that_is_too_long}    Set Variable    value    # 44
    EXCEPT    *fatal*    AS    ${too_loong_name_for_captured_error_message}    # 41
        No Operation
    EXCEPT    *****    AS    ${another_too_long_name_for_captured_error_message}    # 48
        # Making sure that except branch is visited:
        Set Local Variable    ${different_local_variable_name_that_is_too_long}    value    # 46
        # Below is not re-reported: Variables from TRY branch still in scope:
        ${local_variable_name_that_is_way_tooo_long}    Set Variable    value
    EXCEPT
        No Operation
    ELSE
        Set Task Variable    $different_suite_variable_name_that_is_too_long    value    # 46
    FINALLY
        No Operation
    END


*** Keywords ***
Some Keyword
    TRY
        No Operation
    EXCEPT    AS    ${too_loong_name_for_captured_error_message}    # 41
        No Operation
    END
