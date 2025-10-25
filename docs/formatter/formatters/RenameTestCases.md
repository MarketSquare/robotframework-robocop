# RenameTestCases

Enforce test case naming. This formatter capitalizes the first letter of the test case name, removes the trailing dot and
strips leading/trailing whitespaces. If ``capitalize_each_word`` is ``True``, will capitalize each word in test case name.

{{ enable_hint("RenameTestCases") }}

It is also possible to configure ``replace_pattern`` parameter to find and replace a regex pattern. Use ``replace_to``
to set a replacement value. This configuration:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select RenameTestCases -c RenameTestCases.replace_pattern=[A-Z]{3,}-\d{2,} -c RenameTestCases.replace_to=foo
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "RenameTestCases"
    ]
    configure = [
        "RenameTestCases.replace_pattern=[A-Z]{3,}-\d{2,}",
        "RenameTestCases.replace_to=foo"
    ]
    ```

replaces all occurrences of a given pattern with string 'foo':

=== "Before"

    ```robotframework
    *** Test Cases ***
    test ABC-123
        No Operation
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    Test foo
        No Operation
    ```

## Capitalize each word

If you set ``capitalize_each_word`` to ``True`` it will capitalize each word in the test case name:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select RenameTestCases -c RenameTestCases.capitalize_each_word=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "RenameTestCases"
    ]
    configure = [
        "RenameTestCases.capitalize_each_word=True"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Test Cases ***
    compare XML with json
        No Operation
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    Compare XML With Json
        No Operation
    ```
