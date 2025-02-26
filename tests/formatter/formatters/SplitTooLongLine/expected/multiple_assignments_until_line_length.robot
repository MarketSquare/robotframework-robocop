*** Keywords ***
Multiple Assignments
    ${first_assignment}    ${second_assignment}    My Keyword
    ${first_assignment}
    ...    ${second_assignment}
    ...    Some Lengthy Keyword So That This Line Is Too Long    ${arg1}    ${arg2}
    ${multiline_first}
    ...    ${multiline_second}=
    ...    Some Lengthy Keyword So That This Line Is Too Long
    ${first_assignment}
    ...    ${second_assignment}
    ...    ${third_assignment}
    ...    Some Lengthy Keyword So That This Line Is Too Long And Bit Over    ${arg1}    ${arg2}
