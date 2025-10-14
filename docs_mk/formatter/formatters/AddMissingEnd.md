# AddMissingEnd

Add missing `END` token to FOR loops and IF statements.

> **Note:** This formatter is enabled by default.

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

Skip formatting
----------------

It is possible to use the following arguments to skip formatting of the code:

- :ref:`skip sections`

It is also possible to use disablers (:ref:`disablers`) but ``skip`` option
makes it easier to skip all instances of a given code type.
