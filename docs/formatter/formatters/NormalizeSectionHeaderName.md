# NormalizeSectionHeaderName

Normalize section header names.

{{ configure_hint("NormalizeSectionHeaderName") }}

Robot Framework is quite flexible with the section header naming. The following lines are equal:

```robotframework
*setting
*** SETTINGS
*** SettingS ***
```

This formatter normalize naming to follow ``*** SectionName ***`` format (with the plural variant):

```robotframework
*** Settings ***
*** Keywords ***
*** Test Cases ***
*** Variables ***
*** Comments ***
```

Optional data after section header (for example data driven column names) is preserved.
It is possible to upper case section header names by passing ``uppercase=True`` parameter:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure NormalizeSectionHeaderName.uppercase=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "NormalizeSectionHeaderName.uppercase=True"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    * setting *
    ```

=== "After"

    ```robotframework
    *** SETTINGS ***
    ```

## Skip formatting

It is possible to use the following arguments to skip formatting of the code:

- [skip sections](../skip_formatting.md#skip-sections)

It is also possible to use [disablers](../../configuration/disablers.md) but ``skip`` option makes it easier to skip
all instances of a given type of the code.
