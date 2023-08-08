TRY/EXCEPT with shared variables scope for all branches (#925)
--------------------------------------------------------------

``variable-overwritten-before-usage`` will no longer be raised  if the same variable names are used in different
branches of the ``TRY/EXCEPT`` block::

    *** Test Cases ***
    Example Test
        TRY
            ${value}    Possibly Failing Keyword
        EXCEPT
            ${value}    Set Variable    Keyword failed  # each TRY/EXCEPT/ELSE/FINALLY branch is now separate scope
        END
        Log To Console    ${value}
