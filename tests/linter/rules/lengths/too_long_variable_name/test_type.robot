*** Settings ***
Documentation       This tests ignoring of type conversions added in RF 7.3

*** Variables ***
${SHORT_SUITE_VARIABLE_NAME: int}      10
${OTHER_SUITE_VARIABLE_NAME: dict[int, str]}    {3278: 'Critical', 4173: 'High', 5334: 'High'}
${YET_ANOTHER_SUITE_VARIABLE_NAME: int | float}    ${{math.pi}}
${SOME_EVEN_LOOOOOONGER_SUITE_VARIABLE_NAME: int}     value    # 41
&{OTHER_EVEN_LOOOOONGER_SUITE_VARIABLE_NAME: int=str}    3278=Critical    4173=High    5334=High    # 41

*** Test Cases ***
Test
    VAR    ${short_enough_variable_name_with_type: int}    value

    ${different_short_variable_name: dict[int, str]}    ${different_even_longer_local_variable_name: float}    Some Keyword    # 41

    FOR    ${too_loooooooooong_iteration_variable_name: int}    IN RANGE    ${10}    # 41
        ${short_enough_variable_name_with_type: int}    ${yet_another_even_longer_local_variable_name: dict[int, str]}    Some Other Keyword    # 43
    END

*** Keywords ***
Some Keyword
    [Arguments]    ${short_argument_name_with_long_type: dict[int, str]}    ${keyword_argument_name_that_is_too_long_with_type: int}    # 48
    FOR    ${short_enough_iteration_variable_name: tuple[str, date]}    IN ENUMERATE   2023-06-15    2025-05-30    today
        No Operation
    END

Keyword With ${a_short_embedded_argument_name: dict[int, str]} And ${another_too_looong_embedded_argument_name: float} To Do Something With    # 41
    VAR    ${some_even_loooooonger_local_variable_name: int}    value    # 41

Deadline Is ${given_by_this_argument: date:\d{4}-\d{2}-\d{2}} But ${this_other_date_argument_is_way_too_loong: date:\d{4}-\d{2}-\d{2}}    # 41
    Comment    Embedded keyword arguments containing type and pattern
