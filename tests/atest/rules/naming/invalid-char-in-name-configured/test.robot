*** Test Cases ***
Test with not allowed variable ${var}
    Steps

*** Keywords ***
Keyword?
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail

Keyword With ${em.bedded}$ Argument{}
    No Operation

Keyword With :
    No Operation
