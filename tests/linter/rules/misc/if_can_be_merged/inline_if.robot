*** Keywords ***
Not adjacent with return
    [Documentation]    doc
    IF    $condition    Keyword2    ${arg}

    ${var}    IF    $condition    Keyword2    ${arg}
    IF    $condition    Keyword2    ${arg}    ELSE    Keyword3

    ${var}    IF    $condition    Keyword2    ${arg}
    ${var2}    IF    $condition    Keyword2    ${arg}

    ${var}    IF    $condition    Keyword2    ${arg}
    ${var}    ${var}    IF    $condition    Keyword2    ${arg}

Not adjacent no return
    IF    $condition    Keyword2    ${arg}
    IF    $condition    Keyword2    ${arg}    ELSE    Keyword3

Adjacent with return
    ${var}    IF    $condition    Keyword2    ${arg}
    ${var}    IF    $condition    Keyword2    ${arg}


Adjacent with no return
    IF    $condition    Keyword2    ${arg}    ELSE    Keyword3
    IF    $condition    Keyword2    ${arg}    ELSE    Keyword3

Block and inline with return
    ${var}    IF    $condition    Keyword2    ${arg}
    IF    $condition
        Keyword2    ${arg}
    END
