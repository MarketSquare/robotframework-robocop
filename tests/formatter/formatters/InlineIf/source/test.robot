*** Test Cases ***
Inline IF
    IF    $condition1    Keyword    argument
    IF    $condition1    Keyword    ELSE IF    $condition2    Keyword2    ELSE    Keyword3
    ${var}    IF    $condition1    Keyword    argument

Simple IF
    IF    $condition1
        Keyword    argument
    END
    IF    $condition2
        RETURN
    END

Branched IF
    IF    $condition1
        Keyword    1
    ELSE
        Keyword    2
    END

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
        IF    $condition2
            RETURN
        END
        Keyword
    END

    IF  $condition1
        Keyword
    ELSE
        IF  $condition2
            RETURN
        END
    END

Assign vars IF
   IF    $condition1
       ${var}    Keyword
   END

   IF  $condition1
       ${var}    ${var2}    Keyword
   ELSE
       ${var}    ${var2}    Keyword2
   END

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
        IF    $condition2
            CONTINUE
        END
        Keyword
        IF    $condition3
            BREAK
        END
    END

Multiline IF
    IF    $condition
        Keyword
        ...  1
        ...  2
        ...  3
    END

Return With Value IF
    IF  $condition
       RETURN  ${a}
       ...  ${b}
    END

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
    IF    ${WINDOWS}
        ${user} =    Get Windows User
    ELSE
        ${user} =    Get Posix User
    END

    IF    ${WINDOWS}
        ${user} =    Get Windows User
    ELSE
        ${user}    Get Posix User
    END

    IF    ${WINDOWS}
        ${user}    Get Windows User
    ELSE
        ${user}=    Get Posix User
    END

Short IF that didn't replace
    IF    ${True}
        Log Many    @{ARGS WITH ELSE}
    END

    IF    ${True}
        No Operation
    ELSE
        Fail
    END

    IF    "${version}"
        Version Should Match    ${version}
    END

Too long inline IF
    ${var}    ${var2}    IF    $condition != $condition2    Longer Keyword Name    ${argument}    values    ELSE IF    $condition2    Short Keyword    ${arg}  # comment

    IF    $conditiooooooooon >= $conditiooooooooon    Overly Long Keyword To Replicate Inline If Transformation    ${argument}

    IF    $conditiooooooooon >= $conditiooooooooon    Overly Long Keyword To Replicate Inline If Transformation    ${argument}  # first comment
    ...  ${argument2}  # second comment       with edge case

    IF    $conditiooooooooon >= $conditiooooooooon    Overly Long Keyword To Replicate    ELSE    Keyword That    ${fit}

    IF    $conditiooooooooon >= $conditiooooooooon    Overly Long Keyword To Replicate    ELSE    Keyword That    ${fits}

    ${variable}=    IF    $conditiooooooooon >= $conditiooooooooon    Overly Long Keyword To Replicate    ELSE    Keyword That    ${fits}

    IF    $cond    Short  # leave comment
    IF    $cond    Short But Multiline
    ...    ${arg}

    IF    $cond
    ...    Keyword
    ...    ${arg}

    IF    $cond    Short But Multiline
    ...    ${arg}
    ...    ELSE    Keyword

    IF
    ...    $cond
    ...    Keyword
    ...    ${arg}

If with multiple comments
    IF    ${True}    # comment here is ok
        Log    K1    # Here is also ok
    ELSE IF    ${True}    # Again totally fine
        K2    # Here is also ok
    ELSE    # Here is also ok
        K3    # Here is also ok
    END    # Here is also ok

If with empty values
    IF    $cond    Short But Multiline
    ...    
    ...    ELSE    Keyword

    IF    $cond    Short But Multiline
    ...
    ...    ELSE    Keyword
    ...    # and comment
