# AddMissingEnd

Add missing `END` token to FOR loops and IF statements.

{{ configure_hint("AlignSettingsSection") }}

=== "Before"

    ```robotframework
    *** Test Cases ***
    Test
        FOR    ${x}    IN    foo    bar
            Log    ${x}
        IF    ${condition}
            Log    ${x}
            IF    ${condition}
                Log    ${y}
        Keyword
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    Test
        FOR    ${x}    IN    foo    bar
            Log    ${x}
        END
        IF    ${condition}
            Log    ${x}
            IF    ${condition}
                Log    ${y}
            END
        END
        Keyword
    ```

## Skip formatting

It is possible to use the following arguments to skip formatting of the code:

- [skip sections](../skip_formatting.md#skip-sections)

It is also possible to use [disablers](../../configuration/disablers.md) but ``skip`` option
makes it easier to skip all instances of a given code type.
