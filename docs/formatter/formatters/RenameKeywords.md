# RenameKeywords

Enforce keyword naming. Title Case is applied to the keyword name and underscores are replaced by spaces. It has only
basic support for keywords with embedded variables - use it at your own risk.

{{ enable_hint("RenameKeywords") }}

You can keep underscores if you set ``remove_underscores`` to ``False``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select RenameKeywords -c RenameKeywords.remove_underscores=False
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "RenameKeywords"
    ]
    configure = [
        "RenameKeywords.remove_underscores=False"
    ]
    ```

## Keyword case

By default, each word in the keyword case is capitalized. It can be configured using ``keyword_case`` parameter:

=== "Before"

    ```robotframework
    *** Keywords ***
    keyword name
        Log    ${GLOBAL}
        perform Action
    ```

=== "keyword_case = capitalize_words (default)"

    ```robotframework
    *** Keywords ***
    Keyword Name
        Log    ${GLOBAL}
        Perform Action
    ```

=== "keyword_case = capitalize_first"

    ```robotframework
    *** Keywords ***
    Keyword name
        Log    ${GLOBAL}
        Perform Action
    ```

=== "keyword_case = ignore"

    ```robotframework
    *** Keywords ***
    keyword name
        Log    ${GLOBAL}
        perform Action
    ```

## Library name

By default, the library name in the keyword name is ignored. Anything before the last dot in the name is considered as
a library name. Use `ignore_library = True` parameter to control if the library name part (Library.Keyword) of keyword call
should be renamed.

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        library_name.keyword
    ```

=== "ignore_library = True"

    ```robotframework
    *** Keywords ***
    Keyword
        library_name.Keyword
    ```

=== "ignore_library = False"

    ```robotframework
    *** Keywords ***
    Keyword
        Library Name.Keyword
    ```

## Replace pattern

It is also possible to configure ``replace_pattern`` parameter to find and replace regex pattern. Use ``replace_to``
to set replacement value. This configuration (underscores are used instead of spaces):

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select RenameKeywords -c RenameKeywords.replace_pattern=(?i)^rename\s?me$ -c RenameKeywords.replace_to=New_Shining_Name
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "RenameKeywords"
    ]
    configure = [
        "RenameKeywords.replace_pattern=(?i)^rename\s?me$",
        "RenameKeywords.replace_to=New_Shining_Name"
    ]
    ```

replaces all occurrences of name ``Rename Me``` (case insensitive thanks to ``(?i)`` flag) to ``New Shining Name``:

=== "Before"

    ```robotframework
    *** Keywords ***
    rename Me
       Keyword Call
    ```

=== "After"

    ```robotframework
    *** Keywords ***
    New Shining Name
        Keyword Call
    ```

This feature makes this formatter a convenient tool for renaming your keywords across a Robot Framework project.
