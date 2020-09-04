*** Test Cases ***
Keyword With Nested For Loop
    FOR  ${i}  IN  ${index}
        FOR  ${a}  IN  ${elems}
            Log  ${i}{a}
        END
    END


*** Keywords ***
Keyword With Nested For Loop
    FOR  ${i}  IN  ${index}
        FOR  ${a}  IN  ${elems}
            Log  ${i}{a}
        END
    END

Keyword With Double Nested For Loop
    FOR  ${i}  IN  ${index}
        FOR  ${a}  IN  ${elems}
            FOR  ${a}  IN  ${elems}
                Log  ${i}{a}
            END
        END
    END