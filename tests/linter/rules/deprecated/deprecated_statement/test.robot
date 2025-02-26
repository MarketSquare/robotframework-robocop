*** Settings ***
Suite Setup  Run Keyword If
Suite Teardown  Run Keyword If
Force Tags         tag

Test Setup  Run Keyword If
Test Teardown  Run Keyword If

*** Test Cases ***
Test
    [Setup]  Run Keyword Unless
    [Teardown]  Run Keyword Unless
    Run Keyword Unless   True   Hello World
    Run Keyword If   True   Hello World
    run_keyword_unless   True   Hello World
    builtin.run_KeywoRD_UNLESS   True   Hello World
    BuiltIn.Run Keyword Unless   True   Hello World

Templated test
    [Template]    Run Keyword Unless

*** Keywords ***
CONTINUE and BREAK
    FOR    ${var}  IN RANGE  10
        WHILE    $var
            Continue For Loop
            Continue For Loop If  $var > 10
            Exit For Loop If  $var < 0
            BuiltIn.Exit For Loop
        END
    END

RETURN
    Return From Keyword If  $GLOBAL > 10
    BuiltIn.Return From Keyword
    RETURN
    [Return]
