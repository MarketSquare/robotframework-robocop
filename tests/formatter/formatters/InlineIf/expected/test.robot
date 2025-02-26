*** Test Cases ***
Inline IF
    IF    $condition1    Keyword    argument
    IF    $condition1
        Keyword
    ELSE IF    $condition2
        Keyword2
    ELSE
        Keyword3
    END
    ${var}    IF    $condition1    Keyword    argument

Simple IF
    IF    $condition1    Keyword    argument
    IF    $condition2    RETURN

Branched IF
    IF    $condition1    Keyword    1    ELSE    Keyword    2

    IF    $condition3
        Keyword
    ELSE IF    ${ROOT}
        Keyword2
    ELSE
        Keyword3
    END

Multi statements IF
    IF    $condition1
        Keyword
        Keyword 2
    END

    IF    $condition1
        Keyword
    ELSE IF  $condition2
        Keyword
        Keyword 2
    END

Nested IF
    IF    $condition1
        IF    $condition2    RETURN
        Keyword
    END

    IF  $condition1
        Keyword
    ELSE
        IF    $condition2    RETURN
    END

Assign vars IF
   IF    $condition1
       ${var}    Keyword
   END

   ${var}    ${var2}    IF    $condition1    Keyword    ELSE    Keyword2

   IF  $condition1
       ${var}    Keyword
   ELSE IF  $condition2
       ${var}    Keyword2
   END

   IF  $condition1
       ${var}    Keyword
   ELSE
       ${var2}    Keyword2
   END

   IF  $condition1
       ${var}    Keyword
   ELSE
       Keyword2
   END

Long line IF
    IF    ($condition1 and $condition2) or ($condition3)
        This Keyword Does Some Thing And Have Quite Long Name For Some Reason    ${argument}
    END

For Loop IF
    IF    $condition1
        FOR    ${var}    IN RANGE  10
            Keyword
        END
    END

With Comments IF
    IF    $condition1
        Keyword
    ELSE
        # not sure if it's valid though
    END

Break Continue IF
    WHILE    $condition
        IF    $condition2    CONTINUE
        Keyword
        IF    $condition3    BREAK
    END

Multiline IF
    IF    $condition    Keyword    1    2    3

Return With Value IF
    IF    $condition    RETURN    ${a}    ${b}

Mixed Type Return IF
    IF    $condition
        ${var}    Keyword
    ELSE
        RETURN
    END

Invalid IF
    IF    $condition
    END

    IF    $cond    Keyword
        Keyword
    END

Assignment types
    ${user} =    IF    ${WINDOWS}    Get Windows User    ELSE    Get Posix User

    ${user} =    IF    ${WINDOWS}    Get Windows User    ELSE    Get Posix User

    ${user}    IF    ${WINDOWS}    Get Windows User    ELSE    Get Posix User

Short IF that didn't replace
    IF    ${True}    Log Many    @{ARGS WITH ELSE}

    IF    ${True}    No Operation    ELSE    Fail

    IF    "${version}"    Version Should Match    ${version}

Too long inline IF
    # comment
    IF    $condition != $condition2
        ${var}    ${var2}    Longer Keyword Name    ${argument}    values
    ELSE IF    $condition2
        ${var}    ${var2}    Short Keyword    ${arg}
    ELSE
        ${var}    ${var2}    Set Variable    ${None}    ${None}
    END

    IF    $conditiooooooooon >= $conditiooooooooon
        Overly Long Keyword To Replicate Inline If Transformation    ${argument}
    END

    # first comment
    # second comment       with edge case
    IF    $conditiooooooooon >= $conditiooooooooon
        Overly Long Keyword To Replicate Inline If Transformation    ${argument}    ${argument2}
    END

    IF    $conditiooooooooon >= $conditiooooooooon
        Overly Long Keyword To Replicate
    ELSE
        Keyword That    ${fit}
    END

    IF    $conditiooooooooon >= $conditiooooooooon
        Overly Long Keyword To Replicate
    ELSE
        Keyword That    ${fits}
    END

    IF    $conditiooooooooon >= $conditiooooooooon
        ${variable}=    Overly Long Keyword To Replicate
    ELSE
        ${variable}=    Keyword That    ${fits}
    END

    IF    $cond    Short  # leave comment
    IF    $cond    Short But Multiline    ${arg}

    IF    $cond    Keyword    ${arg}

    IF    $cond    Short But Multiline    ${arg}    ELSE    Keyword

    IF    $cond    Keyword    ${arg}

If with multiple comments
    # comment here is ok
    # Here is also ok
    # Here is also ok
    # Again totally fine
    # Here is also ok
    # Here is also ok
    # Here is also ok
    IF    ${True}    Log    K1    ELSE IF    ${True}    K2    ELSE    K3

If with empty values
    IF    $cond    Short But Multiline    ${EMPTY}    ELSE    Keyword

    # and comment
    IF    $cond
        Short But Multiline    ${EMPTY}
    ELSE
        Keyword    ${EMPTY}
    END
