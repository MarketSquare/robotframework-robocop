*** Keywords ***
Disabled On Keyword    # robocop: off=nesting-depth-keyword
    FOR    ${a}    IN    1
        IF    $a
            FOR    ${b}    IN    1
                IF    $b
                    FOR    ${c}    IN    1
                        Log    deep
                    END
                END
            END
        END
    END

Disabled On Block
    FOR    ${a}    IN    1
        IF    $a
            FOR    ${b}    IN    1
                IF    $b    # robocop: off=nesting-depth-keyword
                    FOR    ${c}    IN    1
                        Log    deep
                    END
                END
            END
        END
    END

Other Rule Disabled
    FOR    ${a}    IN    1    # robocop: off=cognitive-complexity-keyword
        IF    $a
            FOR    ${b}    IN    1
                IF    $b
                    FOR    ${c}    IN    1
                        Log    deep
                    END
                END
            END
        END
    END
