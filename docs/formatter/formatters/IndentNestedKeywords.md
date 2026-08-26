# IndentNestedKeywords

Format indentation inside run keywords variants such as ``Run Keywords`` or ``Run Keyword And Continue On Failure``.

{{ enable_hint("IndentNestedKeywords") }}

Keywords inside run keywords variants are detected and whitespace is formatted to outline them.

=== "Before"

    ```robotframework
    *** Test Cases ***
    Test
        Run Keyword    Run Keyword If    ${True}    Run keywords   Log    foo    AND    Log    bar    ELSE    Log    baz
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    Test
        Run Keyword
        ...    Run Keyword If    ${True}
        ...        Run keywords
        ...            Log    foo
        ...            AND
        ...            Log    bar
        ...    ELSE
        ...        Log    baz
    ```

## Handle AND inside Run Keywords

``AND`` argument inside ``Run Keywords`` can be handled in different ways.

You can configure it using ``indent_and``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select IndentNestedKeywords -c IndentNestedKeywords.indent_and=split_and_indent
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "IndentNestedKeywords"
    ]
    configure = [
        "IndentNestedKeywords.indent_and=split_and_indent"
    ]
    ```

 The following values are available:

- ``indent_and=split`` splits ``AND`` to new line,
- ``indent_and=split_and_indent`` splits ``AND`` and additionally indents the keywords,
- ``indent_and=keep_in_line`` keeps ``AND`` next to the previous keyword.

=== "indent_and=split (default)"

    ```robotframework
    *** Test Cases ***
    Test
        Run keywords
        ...    Log    foo
        ...    AND
        ...    Log    bar
    ```

=== "indent_and=split_and_indent"

    ```robotframework
    *** Test Cases ***
    Test
        Run keywords
        ...        Log    foo
        ...    AND
        ...        Log    bar
    ```

=== "indent_and=keep_in_line"

    ```robotframework
    *** Test Cases ***
    Test
        Run keywords
        ...    Log    foo    AND
        ...    Log    bar
    ```


## Comments

Comments are kept together with the code they refer to. A comment that trails data on a line (for example a
``# robocop: fmt: off`` disabler) stays on the same output line as the closest keyword or argument, instead of being
moved in front of the whole statement:

=== "Before"

    ```robotframework
    *** Test Cases ***
    Test
        Run Keywords    Log    1    AND    Log    2    # keep me next to log 2
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    Test
        Run Keywords
        ...    Log    1
        ...    AND
        ...    Log    2    # keep me next to log 2
    ```

Comments that occupy their own line are kept as standalone comment lines placed before the formatted statement.

## Skip formatting settings

To skip formatting run keywords inside settings (such as ``Suite Setup``, ``[Setup]``, ``[Teardown]`` etc.) set
``skip_settings`` to ``True``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select IndentNestedKeywords -c IndentNestedKeywords.skip_settings=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "IndentNestedKeywords"
    ]
    configure = [
        "IndentNestedKeywords.skip_settings=True"
    ]
    ```
