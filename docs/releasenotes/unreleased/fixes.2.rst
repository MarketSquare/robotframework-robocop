unused-variable not detected within IF block (#1093)
----------------------------------------------------

If the variable was defined in the IF block, I0920 ``unused-variable`` was not reported even if variable was not used
anywhere::

    *** Test Cases ***
    Useless variable definition
        IF    True
             ${not_used}    Keyword Call
        END
