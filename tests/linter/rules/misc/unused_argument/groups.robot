*** Keywords ***
Used in GROUP name
    [Arguments]    ${argument}
    GROUP    Name with ${argument}
        No Operation
    END

Used In GROUP body
    [Arguments]    ${argument}
    GROUP    Named
        Log    ${argument}
    END
