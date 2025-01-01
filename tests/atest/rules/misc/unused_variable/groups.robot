*** Test Cases ***
Used in GROUP name
    ${variable}    Keyword Call
    GROUP    Name with ${variable}
        No Operation
    END

Used in GROUP body
    ${variable}    Keyword Call
    GROUP    Named
        Log    ${variable}
    END

Unused defined in GROUP
    GROUP    Named
        ${variable}    Keyword Call
        ${used}    Keyword Call
    END
    Log    ${used}
