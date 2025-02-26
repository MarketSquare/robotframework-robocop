*** Keywords ***
Inline IF
    [Arguments]    ${arg}
    IF    $cond    Keyword

    IF  $cond    Keyword  1  ELSE IF    Keyword2    ${arg}

    IF  ${variable} == 5
      IF    $cond               Keyword
    END

    ${var}    IF    $cond    Keyword
    ...  ${arg}

    FOR    ${var}    IN RANGE    10
        FOR    ${var2}    1  2
        IF    $cond    Keyword
        END
    END

WHILE
    WHILE  $cond
      Keyword With  ${arg}
      ...    ${arg2}
    IF  ${variable} == 5
      IF    $cond               Keyword
    END
    END

TRY EXCEPT
    TRY
     Some Keyword
    EXCEPT    Error message    # Try matching this first.
        Error Handler 1
    END

    TRY
        IF    $cond    Keyword
    EXCEPT    Error message    Another error    ${message}  # Match any of these.
      Error handler
      TRY
                    Other Stuff
      EXCEPT
      Quite Nested
      ELSE
          Is It not?
      END
    END
    Open Connection

    TRY
      Use Connection
    FINALLY
          Close Connection
    END

Nested IF 1
    [Documentation]    FAIL Inline IF cannot be nested.
    IF    True    IF    True    Not run

Nested IF 2
    [Documentation]    FAIL Inline IF cannot be nested.
    IF    True    Not run    ELSE    IF    True    Not run

Nested IF 3
    [Documentation]    FAIL Inline IF cannot be nested.
    IF                True    IF    True    Not run
    ...    ELSE IF    True    IF    True    Not run
    ...    ELSE               IF    True    Not run
