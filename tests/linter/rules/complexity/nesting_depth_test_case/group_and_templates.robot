*** Settings ***
Test Template    Run Case


*** Test Cases ***
Templated Test Case
    [Template]    Run Case
    first    second
    third    fourth

Group In Test Case
    GROUP    Outer
        FOR    ${a}    IN    1
            GROUP    Inner
                IF    $a
                    WHILE    $a
                        TRY
                            Log    ${a}
                        END
                    END
                END
            END
        END
    END

Variable Declarations
    VAR    ${x}    1
    FOR    ${a}    IN    1
        VAR    ${y}    2
        IF    $a
            VAR    ${z}    3
        END
    END
