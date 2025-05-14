*** Keywords ***
Keyword With Try
    [Arguments]    ${expected_error}
    ${local} =    Keyword
    TRY
        Do Stuff    ${local}    ${GLOBAL}
    EXCEPT    Error    AS    ${error}
        Log    ${error}
    END

    TRY
        No Operation
    EXCEPT    ${expected_error}
        No Operation
    END

WHILE with limit
    [Arguments]    ${ar_gument}
    WHILE    ${True}    limit=${ar_gument}
        No Operation
    END
