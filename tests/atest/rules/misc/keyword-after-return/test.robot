*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    [Return]    ${var}
    Fail

RETURN valid
    [Documentation]  this is doc
    No Operation
    IF    $condition
        RETURN
    END
    WHILE    $condition
        Keyword
        RETURN
    END
    FOR    ${var}    IN RANGE  10
        Keyword
        RETURN
    END
    TRY
        Keyword
        RETURN
    EXCEPT
        Keyword
        RETURN
    FINALLY
        Keyword
        RETURN
    END
    FOR    ${var}    IN    @{LIST}
        RETURN
        RETURN
    END
    RETURN

RETURN invalid
    [Documentation]  this is doc
    No Operation
    IF    $condition
        RETURN
        Keyword
    END
    WHILE    $condition
        RETURN
        Keyword
    END
    FOR    ${var}    IN RANGE  10
        RETURN
        Keyword
    END
    TRY
        RETURN
        Keyword
    EXCEPT
        RETURN
        Keyword
    FINALLY
        RETURN
        IF    $condition    RETURN
    END
    RETURN
    No Operation
    FOR    ${var}    IN    @{LIST}
        RETURN
        Keyword
        RETURN
    END
