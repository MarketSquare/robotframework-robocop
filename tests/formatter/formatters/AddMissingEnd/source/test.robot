*** Test Cases ***
Missing In For
    FOR    ${x}    IN    foo    bar
        Log    ${x}
    Keyword

Missing In Nested For
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        FOR  ${y}    IN    bar    foo
            Log    ${y}
    END
    Keyword

Missing In Nested For 2
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        FOR  ${y}    IN    bar    foo
            Log    ${y}
        END
    Keyword

Missing In Nested For 3
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        FOR  ${y}    IN    bar    foo
            Log    ${y}
    Keyword

Missing In For Last Statement
    FOR    ${x}    IN    foo    bar
        Log    ${x}

Missing In For Comments In And After
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        # I belong here

# I'm fine there

Dummy Keyword
    No Operation

Missing In If
    IF    ${condition}
        Keyword

Missing In Nested If
    IF    ${condition}
        Log    ${x}
        IF    ${condition}
            Log    ${y}
    END
    Keyword

Missing In Nested If 2
    IF    ${condition}
        Log    ${x}
        IF    ${condition}
            Log    ${y}
        END
    Keyword

Missing In Nested If 3
    IF    ${condition}
        Log    ${x}
        IF    ${condition}
            Log    ${y}
    Keyword

Missing In If Last Statement
    IF    ${condition}
        Log    ${x}

Missing In If Comments In And After
    IF    ${condition}
        Log    ${x}
        # I belong here

# I'm fine there

Missing In If Else
    IF    ${condition}
        Log    ${x}
    ELSE
        Keyword

Missing In Else If
    IF    ${condition}
        Log    ${x}
    ELSE
        Keyword
    ELSE IF
        Other Keyword

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

Bad Indent
    IF    ${i}==1
    Log    "one"
    END

*** Keywords ***
Missing In For
    FOR    ${x}    IN    foo    bar
        Log    ${x}
    Keyword

Missing In Nested For
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        FOR  ${y}    IN    bar    foo
            Log    ${y}
    END
    Keyword

Missing In Nested For 2
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        FOR  ${y}    IN    bar    foo
            Log    ${y}
        END
    Keyword

Missing In Nested For 3
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        FOR  ${y}    IN    bar    foo
            Log    ${y}
    Keyword

Missing In For Last Statement
    FOR    ${x}    IN    foo    bar
        Log    ${x}

Missing In For Comments In And After
    FOR    ${x}    IN    foo    bar
        Log    ${x}
        # I belong here

# I'm fine there

Dummy Keyword
    No Operation

Missing In If
    IF    ${condition}
        Keyword

Missing In Nested If
    IF    ${condition}
        Log    ${x}
        IF    ${condition}
            Log    ${y}
    END
    Keyword

Missing In Nested If 2
    IF    ${condition}
        Log    ${x}
        IF    ${condition}
            Log    ${y}
        END
    Keyword

Missing In Nested If 3
    IF    ${condition}
        Log    ${x}
        IF    ${condition}
            Log    ${y}
    Keyword

Missing In If Last Statement
    IF    ${condition}
        Log    ${x}

Missing In If Comments In And After
    IF    ${condition}
        Log    ${x}
        # I belong here

# I'm fine there

Missing In If Else
    IF    ${condition}
        Log    ${x}
    ELSE
        Keyword

Missing In Else If
    IF    ${condition}
        Log    ${x}
    ELSE
        Keyword
    ELSE IF
        Other Keyword

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

Nested For With Identical Indent
    FOR    ${x}    IN    x
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
