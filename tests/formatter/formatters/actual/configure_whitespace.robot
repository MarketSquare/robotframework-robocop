*** Keywords ***
Keyword
    IF  ${b} - ${e} <= ${c} and ${b} > 10
        ${a}  Evaluate  ${d} + 2 + (10 - ${c})
    ELSE
        ${a}  Evaluate  ${d} + 2
    END
