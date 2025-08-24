*** Settings ***
Documentation       doc


*** Variables ***
${SHORT_SUITE_VARIABLE_NAME}      value
${SOME_EVEN_LOOOOOONGER_SUITE_VARIABLE_NAME}=    value


*** Test Cases ***
Test
    ${short_variable_name}    Set Variable    value

    ${different_short_variable_name}    ${different_even_longer_local_variable_name} =    Some Keyword

    FOR    ${too_loooooooooong_iteration_variable_name}    IN RANGE    ${10}
        ${some_even_loooooonger_local_variable_name}    ${different_even_longer_local_variable_name}    Some Other Keyword    # reassign existing variables
    END

*** Keywords ***
Some Keyword
    [Arguments]    ${short_argument_name}    ${some_loooooooooooooooooong_argument_name}    ${some_even_loooooooooooonger_argument_name}=default
    FOR    ${too_looooooooooooong_iteration_index_name}    ${too_looooooooooooong_iteration_value_name}    IN ENUMERATE    @{list}
        No Operation
    END

Keyword With ${an_embedded_argument} And ${another_too_looong_embedded_argument_name} To Do Something With
    No Operation
