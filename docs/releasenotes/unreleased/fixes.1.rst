Inline If with assign variables handling variables in invalid order (#987)
---------------------------------------------------------------------------

Inline If did not properly recognized that variables were used inside if loop before assigning return value.
Following code::

    *** Keywords ***
    Keyword With Argument
        [Arguments]    ${arg}
        ${arg}    IF    ${VALUE}    Use  ${arg}

    Keyword With Local Variable
        ${var}    Set Variable    default value
        ${var}    IF    ${VALUE}    Use  ${var}

Will no longer raise W0921 ``argument-overwritten-before-usage`` and W0922 ``variable-overwritten-before-usage``.

And following code::

    *** Keywords ***
    Inline If - Overwritten Variable
        ${var}    Set Variable    default
        ${var}    IF    condition    Use    ${var}

    InlineIf - Assign With The Same Name As Arg
        ${assign}    IF    condition    Do Nothing    ELSE    Use    ${assign}

Should now raise I0920 ``unused-variable`` for ``${var}`` and ``${assign}`` variables.
