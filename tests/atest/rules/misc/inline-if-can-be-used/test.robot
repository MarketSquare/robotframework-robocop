*** Test Cases ***
Short IF
    IF    $condition
        ${var}  Keyword    ${var}
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
        Keyword
    END

Long IF
    IF    $condition
        ${variable}  Keyword That Should Go Over Limit    ${argument1}    something else
    END
