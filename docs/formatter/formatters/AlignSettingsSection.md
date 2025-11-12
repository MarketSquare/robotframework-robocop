# AlignSettingsSection

Align statements in ``*** Settings ***`` section to columns.

{{ configure_hint("AlignSettingsSection") }}

=== "Before"

    ```robotframework
    *** Settings ***
    Library      SeleniumLibrary
    Library   Mylibrary.py
    Variables  variables.py
    Test Timeout  1 min
      # this should be left aligned
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Library         SeleniumLibrary
    Library         Mylibrary.py
    Variables       variables.py
    Test Timeout    1 min
    # this should be left aligned
    ```

## Align up to columns

You can configure how many columns should be aligned to the longest token in the given column. The remaining columns
will use fixed length separator length ``--space-count``. By default, only the first two columns are aligned.

Example of how the ``AlignSettingsSection`` formatter behaves with the default configuration and multiple columns:

=== "Before"

    ```robotframework
    *** Settings ***
    Library    CustomLibrary   WITH NAME  name
    Library    ArgsedLibrary   ${1}  ${2}  ${3}
    
    Documentation     Example using the space separated format.
    ...  and this documentation is multiline
    ...  where this line should go I wonder?
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Library             CustomLibrary    WITH NAME    name
    Library             ArgsedLibrary    ${1}    ${2}    ${3}
    
    Documentation       Example using the space separated format.
    ...                 and this documentation is multiline
    ...                 where this line should go I wonder?
    ```

You can configure it to align three columns:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format -c AlignSettingsSection.up_to_column=3
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "AlignSettingsSection.up_to_column=3"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Settings ***
    Library    CustomLibrary   WITH NAME  name
    Library    ArgsedLibrary   ${1}  ${2}  ${3}
    
    Documentation     Example using the space separated format.
    ...  and this documentation is multiline
    ...  where this line should go I wonder?
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Library             CustomLibrary    WITH NAME    name
    Library             ArgsedLibrary    ${1}         ${2}     ${3}
    
    Documentation       Example using the space separated format.
    ...                 and this documentation is multiline
    ...                 where this line should go I wonder?
    ```

To align all columns set ``up_to_column`` to 0.

## Extra indent for keyword arguments

Arguments in multi-line settings are indented by additional ``argument_indent`` (default ``4``) spaces.
You can configure the indent or disable it by setting ``argument_indent`` to 0.

=== "argument_indent=4 (default)"

    ```robotframework
    *** Settings ***
    Suite Setup         Start Session
    ...                     host=${IPADDRESS}
    ...                     user=${USERNAME}
    ...                     password=${PASSWORD}
    Suite Teardown      Close Session
    ```

=== "argument_indent=2"

    ```robotframework
    *** Settings ***
    Suite Setup         Start Session
    ...                   host=${IPADDRESS}
    ...                   user=${USERNAME}
    ...                   password=${PASSWORD}
    Suite Teardown      Close Session
    ```

=== "argument_indent=0"

    ```robotframework
    *** Settings ***
    Suite Setup         Start Session
    ...                 host=${IPADDRESS}
    ...                 user=${USERNAME}
    ...                 password=${PASSWORD}
    Suite Teardown      Close Session
    ```

``WITH NAME`` arguments are not indented:

=== "Before"

    ```robotframework
    *** Settings ***
    Library             SeleniumLibrary
    ...                 timeout=${TIMEOUT}
    ...                 implicit_wait=${TIMEOUT}
    ...                 run_on_failure=Capture Page Screenshot
    ...                 WITH NAME    Selenium
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Library             SeleniumLibrary
    ...                     timeout=${TIMEOUT}
    ...                     implicit_wait=${TIMEOUT}
    ...                     run_on_failure=Capture Page Screenshot
    ...                 WITH NAME    Selenium
    ```

## Fixed the width of the column

It's possible to set the fixed width of the column. To configure it use ``fixed_width`` parameter:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format -c AlignSettingsSection.fixed_width=30
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "AlignSettingsSection.fixed_width=30
    ]
    ```

This configuration respects ``up_to_column`` parameter but ignores ``argument_indent``.

=== "Before"

    ```robotframework
    *** Settings ***
    Library    CustomLibrary   WITH NAME  name
    Library    ArgsedLibrary   ${1}  ${2}  ${3}
    
    Documentation     Example using the space separated format.
    ...  and this documentation is multiline
    ...  where this line should go I wonder?
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Library                      CustomLibrary   WITH NAME  name
    Library                      ArgsedLibrary   ${1}  ${2}  ${3}
    
    Documentation                Example using the space separated format.
    ...                          and this documentation is multiline
    ...                          where this line should go I wonder?
    ```

## Minimal width of the column

It's possible to set the minimal width of the column. To configure it use ``min_width`` parameter:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format -c AlignSettingsSection.min_width=20
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "AlignSettingsSection.min_width=20"
    ]
    ```

This configuration respects ``up_to_column`` parameter.

=== "Before"

    ```robotframework
    *** Settings ***
    Library    CustomLibrary   WITH NAME  name
    Library    ArgsedLibrary   ${1}  ${2}  ${3}
    
    Documentation     Example using the space separated format.
    ...  and this documentation is multiline
    ...  where this line should go I wonder?
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Library             CustomLibrary   WITH NAME  name
    Library             ArgsedLibrary   ${1}  ${2}  ${3}
    
    Documentation       Example using the space separated format.
    ...                 and this documentation is multiline
    ...                 where this line should go I wonder?
    ```

## Select lines to format

AlignSettingsSection does also support global formatting params ``--start-line`` and ``--end-line``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --start-line 2 --end-line 3 --configure AlignSettingsSection.up_to_column=3
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    start-line = 2
    end-line = 3
    configure = [
        "AlignSettingsSection.up_to_column=3"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Settings ***
    Metadata  Version  2.0  # this should be not aligned
    Metadata      More Info  For more information about *Robot Framework* see http://robotframework.org
    Metadata     Executed At  {HOST}
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Metadata  Version  2.0  # this should be not aligned
    Metadata    More Info       For more information about *Robot Framework* see http://robotframework.org
    Metadata    Executed At     {HOST}
    ```

## Skip formatting

It is possible to use the following arguments to skip formatting of the code:

- [skip option](../skip_formatting.md#skip-option) (``--skip documentation``)

It is highly recommended to use one of the ``skip`` options if you wish to use the alignment, but you have part of the
code that looks better with manual alignment. It is also possible to use [disablers](../../configuration/disablers.md) but ``skip`` option
makes it easier to skip all instances of the given type of code.
