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

# This Is comment
 # Also comment
  # This passes since it's start of another cell

 # Another one

*** Keywords ***
Keyword With Invalid For Loop
    for  ${i}  IN  ${index}
        Log  ${i}
    END

Keyword With Reserved Words
    While
    Continue
    WHILE
    Run Keyword If  ${condition}  Keyword
    ...  Else if  ${condition}  Keyword
    ...  else  Keyword
    Run Keyword If  ${condition}  Keyword
    ...  ELSE IF  ${condition}  Keyword
    ...  ELSE  Keyword
    Run Keyword If  ${condition}  Keyword
    ... ELSE IF  ${condition}  Keyword
    ... ELSE  Keyword

Keyword With Valid For Loop
    FOR  ${i}  ${index}
        Log  ${i}
    END

Keyword With Missing Whitespace After For
    FOR ${i}  IN  ${index}
        Log  ${i}
    END

# This Is comment
 # Also comment
