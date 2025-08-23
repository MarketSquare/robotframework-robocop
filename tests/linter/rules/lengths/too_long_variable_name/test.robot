*** Settings ***
Documentation       doc


*** Variables ***
${SOME_LOOOOOOOOOOOONG_SUITE_VARIABLE_NAME}      value
${SOME_EVEN_LOOOOOONGER_SUITE_VARIABLE_NAME}     value


*** Test Cases ***
Test
    VAR    ${some_loooooooooooong_local_variable_name}    value
    VAR    ${some_even_loooooonger_local_variable_name}    value

    ${different_loooooong_local_variable_name}    Some Keyword
    ${different_even_longer_local_variable_name}    Some Keyword

    ${another_loooooooong_local_variable_name}    ${another_even_looonger_local_variable_name}    Some Other Keyword


*** Keywords ***
Some Keyword
    [Arguments]    ${some_loooooooooooooooooong_argument_name}    ${some_even_loooooooooooonger_argument_name}
    RETURN    value
