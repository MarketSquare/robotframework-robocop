*** Keywords ***
Keyword
    ${a}  Run Keyword If  ${b} - ${e} <= ${c} and ${b} > 10  Evaluate  ${d} + 2 + (10 - ${c})  ELSE  Evaluate  ${d} + 2
