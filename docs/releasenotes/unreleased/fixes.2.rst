Unexpected possible-variable-overwriting when elevating the scope an variable (#1053)
-------------------------------------------------------------------------------------

Using ``VAR`` to elevate scope of the variable should not longer report I0316 ``possible-variable-overwriting``::

    *** Test Cases ***
    ${date}    Get Invoice Date
    VAR    ${DATE}    ${date}    scope=SUITE
