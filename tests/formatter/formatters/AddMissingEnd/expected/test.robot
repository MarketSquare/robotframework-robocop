*** Test Cases ***
Missing In For
    FOR    ${x}    IN    foo    bar
        Log    ${x}
    END
    Keyword

Missing In Nested For
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        FOR  ${y}    IN    bar    foo
            Log    ${y}
        END
    END
    Keyword

Missing In Nested For 2
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        FOR  ${y}    IN    bar    foo
            Log    ${y}
        END
    END
    Keyword

Missing In Nested For 3
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        FOR  ${y}    IN    bar    foo
            Log    ${y}
        END
    END
    Keyword

Missing In For Last Statement
    FOR    ${x}    IN    foo    bar
        Log    ${x}
    END

Missing In For Comments In And After
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        # I belong here
    END

# I'm fine there

Dummy Keyword
    No Operation

Missing In If
    IF    ${condition}
        Keyword
    END

Missing In Nested If
    IF    ${condition}
        Log    ${x}
        IF    ${condition}
            Log    ${y}
        END
    END
    Keyword

Missing In Nested If 2
    IF    ${condition}
        Log    ${x}
        IF    ${condition}
            Log    ${y}
        END
    END
    Keyword

Missing In Nested If 3
    IF    ${condition}
        Log    ${x}
        IF    ${condition}
            Log    ${y}
        END
    END
    Keyword

Missing In If Last Statement
    IF    ${condition}
        Log    ${x}
    END

Missing In If Comments In And After
    IF    ${condition}
        Log    ${x}
        # I belong here
    END

# I'm fine there

Missing In If Else
    IF    ${condition}
        Log    ${x}
    ELSE
        Keyword
    END

Missing In Else If
    IF    ${condition}
        Log    ${x}
    ELSE
        Keyword
    ELSE IF
        Other Keyword
    END

Dummy Keyword 2
    No Operation

Golden If
    IF    ${condition}
        Log    ${x}
    ELSE
        Keyword
    ELSE IF
        Other Keyword
    END

Mixed For and If
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        IF    ${condition}
            Log    foo${x}
        END
    END

Bad Indent
    IF    ${i}==1
    Log    "one"
    END

*** Keywords ***
Missing In For
    FOR    ${x}    IN    foo    bar
        Log    ${x}
    END
    Keyword

Missing In Nested For
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        FOR  ${y}    IN    bar    foo
            Log    ${y}
        END
    END
    Keyword

Missing In Nested For 2
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        FOR  ${y}    IN    bar    foo
            Log    ${y}
        END
    END
    Keyword

Missing In Nested For 3
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        FOR  ${y}    IN    bar    foo
            Log    ${y}
        END
    END
    Keyword

Missing In For Last Statement
    FOR    ${x}    IN    foo    bar
        Log    ${x}
    END

Missing In For Comments In And After
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        # I belong here
    END

# I'm fine there

Dummy Keyword
    No Operation

Missing In If
    IF    ${condition}
        Keyword
    END

Missing In Nested If
    IF    ${condition}
        Log    ${x}
        IF    ${condition}
            Log    ${y}
        END
    END
    Keyword

Missing In Nested If 2
    IF    ${condition}
        Log    ${x}
        IF    ${condition}
            Log    ${y}
        END
    END
    Keyword

Missing In Nested If 3
    IF    ${condition}
        Log    ${x}
        IF    ${condition}
            Log    ${y}
        END
    END
    Keyword

Missing In If Last Statement
    IF    ${condition}
        Log    ${x}
    END

Missing In If Comments In And After
    IF    ${condition}
        Log    ${x}
        # I belong here
    END

# I'm fine there

Missing In If Else
    IF    ${condition}
        Log    ${x}
    ELSE
        Keyword
    END

Missing In Else If
    IF    ${condition}
        Log    ${x}
    ELSE
        Keyword
    ELSE IF
        Other Keyword
    END

Dummy Keyword 2
    No Operation

Golden If
    IF    ${condition}
        Log    ${x}
    ELSE
        Keyword
    ELSE IF
        Other Keyword
    END

Mixed For and If
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        IF    ${condition}
            Log    foo${x}
        END
    END

Nested For With Identical Indent
    FOR    ${x}    IN    x
    END
    FOR    ${y}    IN    y
    FOR    ${z}    IN    z
    Log    ${x}${y}${z}
    END
    END

Bad Indent
    IF    ${i}==1
    Log    "one"
    END

   IF    ${i}>5
   Log    ${i}
   ELSE
   Log    ${i}+1
   END
