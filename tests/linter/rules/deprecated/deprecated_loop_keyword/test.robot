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
