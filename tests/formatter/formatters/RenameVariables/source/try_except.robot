*** Keywords ***
Keyword With Try
    [Arguments]    ${expected_error}
    ${local} =    Keyword
    TRY
        Do Stuff    ${local}    ${global}
    EXCEPT    Error    AS    ${ERROR}
        Log    ${ERROR}
    END

    TRY
        No Operation
    EXCEPT    ${expected error}
        No Operation
    END

WHILE with limit
    [Arguments]    ${ar_gument}
    WHILE    ${True}    limit=${AR GUMENT}
        No Operation
    END
