*** Test Cases ***
Not nested
    GROUP    Solo
        Log    a
    END

Nested
    GROUP    Outer
        GROUP    Inner
            Log    a
        END
    END

Deeply nested
    GROUP    L1
        GROUP    L2
            GROUP    L3
                Log    a
            END
        END
    END
