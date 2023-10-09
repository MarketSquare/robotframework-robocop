*** Test Cases ***
Short IF
    IF    $condition
        Keyword    ${var}
    END

IF with ELSE and ELSE IF
    IF    $condition
        Keyword
    ELSE
        Keyword
    END
    IF    $condition
        Keyword
    ELSE IF    $other
        BREAK
    END

Long IF
    IF    $condition
        ${variable}  Keyword That Should Go Over Limit    ${argument1}    something else
    END

IF With Assign
    IF    ${condition}
        ${assign}    Keyword
    END
    IF    ${condition}
        ${assign}    Keyword
    ELSE
        ${assign}    Keyword2
    END
