*** Settings ***
Documentation  doc


*** Variables ***
${v_ar}       10
${other_var}  20
${V AR}       a
${other_var}  30

${variable}  1
... a
... a
.... a
.... a
.. a
.. a
 ... a
 ... a
${variable2}
 ...  b
 ...  b

*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail
