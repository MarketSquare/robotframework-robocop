*** Keywords ***
Inline IF
    IF    $cond    Keyword
    IF    $cond    Keyword    ELSE    Keyword2    ${var}

WHILE
    # robocop: fmt: off
    WHILE    $cond
        Keyword
        # comment
    Keyword 2
    # robocop: fmt: on

TRY EXCEPT
    # robocop: fmt: off
    TRY
        Some Keyword
    EXCEPT    Error message    # Try matching this first.
        IF    $cond    Keyword
