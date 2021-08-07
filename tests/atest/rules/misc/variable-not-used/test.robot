*** Settings ***
Documentation    This is suite doc


*** Test Cases ***
Test With One Assignment
    [Documentation]   doc
    ${var}    Keyword
    ${var1}    ${var2}    Keyword

Test With Used Assignment
    [Documentation]  Gold test
    ${var}    Keyword
    Log     ${var}

Test With Different Format Variable
    [Documentation]  Gold test
    @{var test}    Keyword
    Log     ${VAR_Test}

Test For Testing Normalize
    [Documentation]  test
    ${var123}    Keyword
    Log     ${var_123}

Test For Redefine Variable But Never Used
    [Documentation]  test
    ${var}    Keyword
    ${var}    Keyword 2
    Log  ${var}

Test Variables With The Same Name
    [Documentation]  test
    ${var}    Keyword    ${var}

Test With Keyword Argument
    [Documentation]  Gold test
    ${var}    Keyword
    Keyword Kwargs  test=${var}

Test With Embedded
    [Documentation]  Gold test
    ${value}    Keyword
    Keyword Argument Value With ${value} Embedded

Test With Extended Variable
    [Documentation]  Gold test
    ${class instance}  Keyword
    ${dict var}  Keyword
    Another Keyword  ${class_instance.attribute}
    Another Keyword  ${dict_var['key']}


*** Keywords ***
Keyword With One Assignment
    [Documentation]  doc
    ${var}    Keyword
    ${var1}    ${var2}    Keyword

Keyword With Used Assignment
    [Documentation]  Gold test
    ${var}    Keyword
    Log     ${var}

Keyword With Different Format Variable
    [Documentation]  Gold test
    @{var test}    Keyword
    Log     ${VAR_Test}

Keyword For Testing Normalize
    [Documentation]  test
    ${var123}    Keyword
    Log     ${var_123}

Keyword For Redefine Variable But Never Used
    [Documentation]  test
    ${var}    Keyword
    ${var}    Keyword 2
    Log  ${var}

Assign Variables With The Same Name
    [Documentation]  test
    ${var}    Keyword    ${var}

Reutrn Variable
    [Documentation]  Gold test
    ${final var}    Keyword
    [Return]   ${final var}

Reutrn Variable WIth W0901
    [Documentation]  Gold test
    [Return]   ${final var}
    ${final var}    Keyword

Keyword With Keyword Argument
    [Documentation]  Gold test
    ${var}    Keyword
    Keyword Kwargs  test=${var}

Keyword Argument Value With Embedded
    [Documentation]  Gold test
    ${value}    Keyword
    Keyword Argument Value With ${value} Embedded

Keyword With Extended Variable
    [Documentation]  Gold test
    ${class instance}  Keyword
    ${dict var}  Keyword
    Another Keyword  ${class_instance.attribute}
    Another Keyword  ${dict_var['key']}
