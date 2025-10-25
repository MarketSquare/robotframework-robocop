# AlignVariablesSection

Align variables in ``*** Variables ***`` section to columns.

{{ configure_hint("AlignVariablesSection") }}

=== "Before"

    ```robotframework
    *** Variables ***
    ${VAR}  1
    ${LONGER_NAME}  2
    &{MULTILINE}  a=b
    ...  b=c
    ```

=== "After"

    ```robotframework
    *** Variables ***
    ${VAR}          1
    ${LONGER_NAME}  2
    &{MULTILINE}    a=b
    ...             b=c
    ```

## Align up to columns

You can configure how many columns should be aligned to the longest token in a given column. The remaining columns
will use fixed length separator length ``--space-count``. By default, only the first two columns are aligned.

Example of how ``AlignVariablesSection`` formatter behaves with default configuration and multiple columns:

=== "Before"

    ```robotframework
    *** Variables ***
    ${VARIABLE 1}  10  # comment
    @{LIST}  a  b  c  d
    ${LONGER_NAME_THAT_GOES_AND_GOES}    longer value that goes and goes
    ```

=== "After"

    ```robotframework
    *** Variables ***
    ${VARIABLE 1}                           10    # comment
    @{LIST}                                 a    b    c    d
    ${LONGER_NAME_THAT_GOES_AND_GOES}       longer value that goes and goes
    ```

You can configure it to align three columns:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure AlignVariablesSection.up_to_column=3
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "AlignVariablesSection.up_to_column=3"
    ]
    ```

will result in the following formatting:
   

=== "Before"

    ```robotframework
    *** Variables ***
    ${VARIABLE 1}  10  # comment
    @{LIST}  a  b  c  d
    ${LONGER_NAME_THAT_GOES_AND_GOES}    longer value that goes and goes
    ```

=== "After"

    ```robotframework
    *** Variables ***
    ${VARIABLE 1}                           10                                  # comment
    @{LIST}                                 a                                   b    c    d
    ${LONGER_NAME_THAT_GOES_AND_GOES}       longer value that goes and goes
    ```

To align all columns set ``up_to_column`` to 0.

## Select variable types to align

It is possible to not align variables of given types. You can choose between following types: ``scalar`` (``$``), ``list`` (``@``),
``dict`` (``&``). Invalid variables - such as missing values or not left-aligned - will always be aligned no matter the type.
You can configure types to skip using ``skip_types`` parameter:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure AlignVariablesSection.skip_types=dict,list
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "AlignVariablesSection.skip_types=dict,list"
    ]
    ```

``skip_types`` accepts a comma-separated list of types.

Using the above configuration code will be aligned in the following way:

=== "Before"

    ```robotframework
    *** Variables ***
    ${VARIABLE 1}  10  # comment
    @{LIST}  a
    ...    b
    ...    c
    ...    d
    ${LONGER_NAME_THAT_GOES_AND_GOES}    longer value that goes and goes
    &{SOME_DICT}    key=value  key2=value
    ```

=== "After"

    ```robotframework
    *** Variables ***
    ${VARIABLE 1}                           10    # comment
    @{LIST}  a
    ...    b
    ...    c
    ...    d
    ${LONGER_NAME_THAT_GOES_AND_GOES}       longer value that goes and goes
    &{SOME_DICT}    key=value  key2=value
    ```

## Fixed width of column

It's possible to set a fixed width of the column. To configure it use ``fixed_width`` parameter:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure AlignVariablesSection.fixed_width=20
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "AlignVariablesSection.fixed_width=20"
    ]
    ```

This configuration respects ``up_to_column`` parameter:

=== "Before"

    ```robotframework
    *** Variables ***
    # some comment

    ${VARIABLE 1}    10    # comment
    @{LIST}                                 a    b    c    d
    ${LONGER_NAME_THAT_GOES_AND_GOES}       longer value that goes and goes

    &{MULTILINE}    a=b
    ...     b=c
    ...     d=1
    ```

=== "After"

    ```robotframework
    *** Variables ***
    # some comment

    ${VARIABLE 1}       10    # comment
    @{LIST}             a    b    c    d
    ${LONGER_NAME_THAT_GOES_AND_GOES}    longer value that goes and goes

    &{MULTILINE}        a=b
    ...                 b=c
    ...                 d=1
    ```

## Minimal width of column

It's possible to set minimal width of the column. To configure it use ``min_width`` parameter:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure AlignVariablesSection.min_width=20
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "AlignVariablesSection.min_width=20"
    ]
    ```

This configuration respects ``up_to_column`` parameter. Example where there is variable longer than ``min_width``:

=== "Before"

    ```robotframework
    *** Variables ***
    # some comment

    ${VARIABLE 1}    10    # comment
    @{LIST}                                 a    b    c    d
    ${LONGER_NAME_THAT_GOES_AND_GOES}       longer value that goes and goes

    &{MULTILINE}    a=b
    ...     b=c
    ...     d=1
    ```

=== "After"

    ```robotframework
    *** Variables ***
    # some comment

    ${VARIABLE 1}                        10    # comment
    @{LIST}                              a    b    c    d
    ${LONGER_NAME_THAT_GOES_AND_GOES}    longer value that goes and goes

    &{MULTILINE}                          a=b
    ...                                   b=c
    ...                                   d=1
    ```

Example where all variables are shorter than ``min_width``:

=== "Before"

    ```robotframework
    *** Variables ***
    # some comment

    ${VARIABLE 1}    10    # comment
    @{LIST}                                 a    b    c    d

    &{MULTILINE}    a=b
    ...     b=c
    ...     d=1
    ```

=== "After"

    ```robotframework
    *** Variables ***
    # some comment

    ${VARIABLE 1}       10    # comment
    @{LIST}             a    b    c    d

    &{MULTILINE}        a=b
    ...                 b=c
    ...                 d=1
    ```

## Select lines to align

AlignVariablesSection does also support global formatting params ``--start-line`` and ``--end-line``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --start-line 5 --end-line 17 --configure AlignVariablesSection.up_to_column=3
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    start-line = 5
    end-line = 17
    configure = [
        "AlignVariablesSection.up_to_column=3"
    ]
    ```

will result in the following formatting:

=== "Before"

    ```robotframework
    *** Settings ***
    Documentation    This is doc


    *** Variables ***
    # some comment

    ${VARIABLE 1}  10  # comment
    @{LIST}  a  b  c  d
    ${LONGER_NAME_THAT_GOES_AND_GOES}    longer value that goes and goes

               &{MULTILINE}  a=b
    ...  b=c
    ...         d=1

    *** Keywords ***
    Keyword
        Keyword Call
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Documentation    This is doc


    *** Variables ***
    # some comment

    ${VARIABLE 1}  10  # comment
    @{LIST}  a  b  c  d
    ${LONGER_NAME_THAT_GOES_AND_GOES}       longer value that goes and goes

    &{MULTILINE}                            a=b
    ...                                     b=c
    ...                                     d=1

    *** Keywords ***
    Keyword
        Keyword Call
    ```
