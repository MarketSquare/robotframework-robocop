*** Test Cases ***
Test
    for  ${i}  IN  ${index}
        Log  ${i}
    END
    FOR  ${i}  ${index}
        Log  ${i}
    END
    FOR ${i}  IN  ${index}
        Log  ${i}
    END

*** Keywords ***
Keyword With Invalid For Loop
    for  ${i}  IN  ${index}
        Log  ${i}
    END

Keyword With Valid For Loop
    FOR  ${i}  ${index}
        Log  ${i}
    END

Keyword With Missing Whitespace After For
    FOR ${i}  IN  ${index}
        Log  ${i}
    END
