Loop variable from keyword argument marked as unused (#868)
-----------------------------------------------------------

If the loop variable originated from the keyword arguments, it was not marked as used:

```
*** Keywords ***
Unused Variable Rule Validation
    [Documentation]    doc
    [Arguments]    ${counter}
    WHILE    ${counter} < 10
        Log To Console    ${counter}
        ${counter}    Evaluate    ${counter} + 1
    END

```
