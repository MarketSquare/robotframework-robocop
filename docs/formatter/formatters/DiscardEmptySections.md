# DiscardEmptySections

Remove empty sections.

{{ configure_hint("DiscardEmptySections") }}

=== "Before"

    ```robotframework
    *** Settings ***


    *** Test Cases ***
    Test
        [Documentation]  doc
        [Tags]  sometag
        Pass
        Keyword
        One More


    *** Keywords ***
    # This section is not considered empty.


    *** Variables ***

    *** Comments ***
    robocop: disable=all
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    Test
        [Documentation]  doc
        [Tags]  sometag
        Pass
        Keyword
        One More


    *** Keywords ***
    # This section is not considered empty.


    *** Comments ***
    robocop: disable=all
    ```

## Remove sections only with comments

Sections are considered empty if there are only empty lines inside.
You can remove sections with only comments by setting ``allow_only_comments`` parameter to False. ``*** Comments ***``
section with only comments is always considered as non-empty:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure DiscardEmptySection.allow_only_comments=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "DiscardEmptySection.allow_only_comments=True"
    ]
    ```

will format only the following section:

=== "allow_only_comments=True (default)"

    ```robotframework
    *** Test Cases ***
    Test
        [Documentation]  doc
        [Tags]  sometag
        Pass
        Keyword
        One More

    *** Keywords ***
    # This section is considered to be empty.

    *** Comments ***
    # robocop: off=all
    ```

=== "allow_only_comments=False"

    ```robotframework
    *** Test Cases ***
    Test
        [Documentation]  doc
        [Tags]  sometag
        Pass
        Keyword
        One More

    *** Comments ***
    # robocop: off=all
    ```

## Skip formatting

It is possible to use the following arguments to skip formatting of the code:

- [skip sections](../skip_formatting.md#skip-sections)

It is also possible to use [disablers](../../configuration/disablers.md) but ``skip`` option makes it easier to skip all instances of a given
type of the code.
