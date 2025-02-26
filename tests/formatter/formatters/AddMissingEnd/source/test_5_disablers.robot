*** Keywords ***
Inline IF
    IF    $cond    Keyword
    IF    $cond    Keyword    ELSE    Keyword2    ${var}

WHILE
    # robotidy: off
    WHILE    $cond
        Keyword
        # comment
    Keyword 2
    # robotidy: on

TRY EXCEPT
    # robotidy: off
    TRY
        Some Keyword
    EXCEPT    Error message    # Try matching this first.
        IF    $cond    Keyword
