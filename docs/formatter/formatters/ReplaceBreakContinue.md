# ReplaceBreakContinue

Replace ``Continue For Loop`` and ``Exit For Loop`` keyword variants with ``CONTINUE`` and ``BREAK`` statements.

???+ note
    Required Robot Framework version: >=5.0

{{ configure_hint("ReplaceBreakContinue") }}

It will replace ``Continue For Loop`` and ``Exit For Loop`` keywords with ``CONTINUE`` and ``BREAK`` respectively:

=== "Before"

    ```robotframework
    *** Test Cases ***
    Test
        WHILE    $flag
            Continue For Loop
        END
        FOR    ${var}    IN    abc
            Exit For Loop
        END
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    Test
        WHILE    $flag
            CONTINUE
        END
        FOR    ${var}    IN    abc
            BREAK
        END
    ```

Conditional variants are also handled. Shorter IFs can be also formatted to inline ``IF`` with [InflineIf](InlineIf.md) formatter:

=== "Before"

    ```robotframework
    *** Test Cases ***
    Test
        WHILE    $flag
            Continue For Loop If    $condition
        END
        FOR    ${var}    IN    abc
            Exit For Loop If    $condition
        END
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    Test
        WHILE    $flag
            IF    $condition
                CONTINUE
            END
        END
        FOR    ${var}    IN    abc
            IF    $condition
                BREAK
            END
        END
    ```

``Continue For Loop`` and ``Exit For Loop`` along with conditional variants outside the loop are ignored.
