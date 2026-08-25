*** Test Cases ***
Short IF
    IF    $condition    Keyword    ${var}

IF With Return
    IF    $condition    RETURN

IF With Break And Continue
    FOR    ${item}    IN    @{items}
        IF    $stop    BREAK
        IF    $skip    CONTINUE
    END

Long IF Not Reported
    IF    $condition
        ${variable}    Keyword That Should Go Over Limit    ${argument1}    something else
    END

IF With Else Not Reported
    IF    $condition
        Keyword
    ELSE
        Keyword
    END
