*** Keywords ***
CONTINUE and BREAK
    FOR    ${var}  IN RANGE  10
        WHILE    $var
            Continue For Loop
            Continue For Loop If  $var > 10
            Exit For Loop If  $var < 0
            BuiltIn.Exit For Loop
        END
    END

RETURN
    Return From Keyword If  $GLOBAL > 10
    BuiltIn.Return From Keyword
    RETURN
    [Return]
