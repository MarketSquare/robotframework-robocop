*** Keywords ***
Group Is Transparent
    GROUP    Outer
        FOR    ${a}    IN    1
            IF    $a
                GROUP    Inner
                    FOR    ${b}    IN    1
                        IF    $b
                            Log    too deep
                        END
                    END
                END
            END
        END
    END

Only Groups
    GROUP    One
        GROUP    Two
            GROUP    Three
                GROUP    Four
                    GROUP    Five
                        Log    no control flow
                    END
                END
            END
        END
    END
    GROUP    Sequential
        IF    $a
            Log    a
        END
    END

Groups Between Blocks
    IF    $a
        GROUP    One
            FOR    ${b}    IN    1
                GROUP    Two
                    IF    $b
                        Log    depth three
                    END
                END
            END
        END
    END
