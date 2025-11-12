# AlignTestCasesSection

Align ``*** Test Cases ***`` section to columns.

{{ enable_hint("AlignTestCasesSection") }}

Align keyword calls and settings into columns with predefined width in test cases.
There are two possible alignment types (configurable via ``alignment_type``):

- ``fixed`` (default): pad the tokens to the fixed width of the column
- ``auto``: pad the tokens to the width of the longest token in the column

The width of the column sets the limit to the maximum width of the column. Default width is ``24``
(see [widths](#widths) for information how to configure it).

With ``fixed`` alignment each column have fixed width (and tokens that does not fit
go into ``overflow`` state - see [overflow](#overflow)).

``auto`` alignment align tokens to the longest token in the column, and the column width can be shorter or equal to
configured width.

See examples of the alignment types:

=== "Before"

    ```robotframework
    *** Test Cases ***
    Test case
        ${short}    Short Keyword    short arg
        ${other_val}    Short Keyword
        ...    arg
        ...    value

    Templated test case
        [Template]    Templated Keyword
        first_arg  second_arg
        value    ${500}
    ```

=== "fixed (default)"

    ```robotframework
    *** Test Cases ***
    Test case
        ${short}                Short Keyword           short arg
        ${other_val}            Short Keyword
        ...                     arg
        ...                     value

    Templated test case
        [Template]    Templated Keyword
        first_arg               second_arg
        value                   ${500}
    ```

=== "auto"

    ```robotframework
    *** Test Cases ***
    Test case
        ${short}        Short Keyword       short arg
        ${other_val}    Short Keyword
        ...             arg
        ...             value

    Templated test case
        [Template]    Templated Keyword
        first_arg    second_arg
        value        ${500}
    ```

The ``auto`` alignment often leads to more compact code. But ``fixed`` setting offers more stability, and adding new,
slightly longer variable or keyword call will not change alignment of the other lines.

## Widths

The column width is configurable via ``widths`` parameter. The default value is ``24``.
It's possible to configure the width of the several columns (using a comma-separated list of integers):

=== ":octicons-command-palette-24: single width"

    ```bash
    robocop format --select AlignTestCasesSection -c AlignTestCasesSection.widths=20
    ```

=== ":material-file-cog-outline: single width"

    ```toml
    [tool.robocop.format]
    select = [
        "AlignTestCasesSection"
    ]
    configure = [
        "AlignTestCasesSection.widths=24"
    ]
    ```

=== ":octicons-command-palette-24: multiple widths"

    ```bash
    robocop format --select AlignTestCasesSection -c AlignTestCasesSection.widths=10,10,24,30
    ```

=== ":material-file-cog-outline: multiple widths"

    ```toml
    [tool.robocop.format]
    select = [
        "AlignTestCasesSection"
    ]
    configure = [
        "AlignTestCasesSection.widths=10,10,24,30"
    ]
    ```

The last width will be used for the remaining columns. In the previous example we configured widths for 4 columns.
The last width (``30``) will be used for 5th, 6th... and the following columns.

Use width ``0`` to disable column width limit. In ``auto`` alignment type it will always align whole column to the
longest token (no matter how long the token is).

## Overflow

Tokens that do not fit in the column go into ``overflow`` state. There are several ways to deal with them (configurable
via ``handle_too_long`` parameter):

- ``overflow`` (default): align token to the next column
- ``compact_overflow``: try to fit next token between current (overflowed) token and the next column
- ``ignore_rest``: ignore remaining tokens in the line
- ``ignore_line``: ignore whole line

See example (for ``fixed`` alignment type and default width ``24``):

=== "Before"

    ```robotframework
    *** Test Cases ***
    Test case
        # keyword call Looo.. does not fit default column width (24)
        ${assign}    Looooooooonger Keyword Name    ${argument}    last
        Short    Short    Short    Short
        Single
        Multi    ${arg}
        ...    ${arg}
    ```

=== "overflow (default)"

    ```robotframework
    *** Test Cases ***
    Test case
        # we are "overflowing" to the next column - taking 24 * 2 = 48 width
        ${assign}               Looooooooonger Keyword Name                     ${argument}             Short
        Short                   Short                   Short                   Short
        Single
        Multi                   ${arg}
        ...                     ${arg}
    ```

=== "compact_overflow"

    ```robotframework
    *** Test Cases ***
    Test case
        # ${argument} is fit between columns, and next argument ("last") is aligned correctly
        ${assign}               Looooooooonger Keyword Name    ${argument}      last
        Short                   Short                   Short                   Short
        Single
        Multi                   ${arg}
        ...                     ${arg}
    ```

=== "ignore_rest"

    ```robotframework
    *** Test Cases ***
    Test case
        # tokens after too long token are not aligned
        ${assign}               Looooooooonger Keyword Name    ${argument}    Short
        Short                   Short                   Short                   Short
        Single
        Multi                   ${arg}
        ...                     ${arg}
    ```

=== "ignore_line"

    ```robotframework
    *** Test Cases ***
    Test case
        # the wole line containing too long token is ignored
        ${assign}    Looooooooonger Keyword Name    ${argument}    Short
        Short                   Short                   Short                   Short
        Single
        Multi                   ${arg}
        ...                     ${arg}
    ```

## Compact overflow

Compact overflow tries to fit too long tokens between the alignment columns.
This behaviour is controlled with ``compact_overflow_limit = 2`` parameter. If more than configured limit columns are
misaligned in a row, the ``overflow`` mode is used instead of ``compact_overflow``.
This behaviour helps in avoiding the situation, where ``compact_overflow`` misalign whole line if most of the tokens
does not fit in the column.

The below example was run with config:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select AlignTestCasesSection -c AlignTestCasesSection.handle_too_long=compact_overflow -c AlignTestCasesSection.widths=24,28,20
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    line-length = 80
    select = [
        "AlignTestCasesSection"
    ]
    configure = [
        "AlignTestCasesSection.handle_too_long=compact_overflow",
        "AlignTestCasesSection.widths=24,28,20"
    ]
    ```

See example:

=== "Before"

    ```robotframework
    *** Test Cases ***
    Test case
        # compact overflow will be used as we only "misalign" two columns in a row
        LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO}    ${TILAUS}    ${OSTOTILAUS}    ${LÄHETYS}    ${TILAUSPVM}

        # more than two columns are misaligned - using "overflow" instead
        LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO_LONGER}    ${TILAUS_OCC}    ${OSTOTILAUS}    ${LÄHETYS}    ${TILAUSPVM}
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    Test case
        # compact overflow will be used as we only "misalign" two columns in a row
        LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO}    ${TILAUS}       ${OSTOTILAUS}       ${LÄHETYS}          ${TILAUSPVM}

        # more than two columns are misaligned - using "overflow" instead
        LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO_LONGER}             ${TILAUS_OCC}       ${OSTOTILAUS}       ${LÄHETYS}          ${TILAUSPVM}
    ```

## Alignment of the indented blocks

Indented blocks (``FOR``, ``IF``, ``WHILE``, ``TRY..EXCEPT..``) are aligned independently.

=== "Before"

    ```robotframework
    *** Test Cases ***
    Test case
        ${assign}    Keyword
        FOR  ${var}  IN  1  2  3
           ${variable}    Keyword    ${var}
           Another Keyword
           FOR  ${var2}  IN  1  2  3
               Short   1   2
               ${assign}    Longer Keyword
               ...    ${multiline}    ${arg}
           END
        END
       Keyword Call    ${value}  # aligned together with keyword call before FOR loop
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    Test case
        ${assign}               Keyword
        FOR    ${var}    IN    1    2    3
            ${variable}             Keyword                 ${var}
            Another Keyword
            FOR    ${var2}    IN    1    2    3
                Short                   1                       2
                ${assign}               Longer Keyword
                ...                     ${multiline}            ${arg}
            END
        END
        Keyword Call            ${value}  # aligned together with keyword call before FOR loop
    ```

Currently, inline IFs are ignored. Block headers (``FOR ${var} IN @{LIST}`` or ``IF  $condition``) are not aligned.

## Split too long lines

``AlignTestCasesSection`` will split the lines if the lines after the alignment would exceed the limits set
in the [SplitTooLongLine](SplitTooLongLine.md) formatter.

???+ note
    Currently, only ``--configure SplitTooLongLine.split_on_every_arg=True`` mode is supported.

Using this configuration (``SplitTooLongLine`` is enabled by default):

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select AlignTestCasesSection -c AlignTestCasesSection --line-length 80
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    line-length = 80
    select = [
        "AlignTestCasesSection"
    ]
    configure = [
        "AlignTestCasesSection.widths=14,24"
    ]
    ```

will result in the following formatting:

=== "Before"

    ```robotframework
    *** Test Cases ***
    Test case
        # fits now but it will not fit after the alignment
        Keyword    argument1    argument2    argument3    argument4

        # does not fit before the alignment
        Longer Keyword Name That Could Happen    argument value with sentence that goes over

        # fits, will not be split
        Keyword    argument
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    Test case
        # fits now but it will not fit after the alignment
        Keyword
        ...           argument1
        ...           argument2
        ...           argument3
        ...           argument4

        # does not fit before the alignment
        Longer Keyword Name That Could Happen
        ...           argument value with sentence that goes over

        # fits, will be aligned but not split
        Keyword       argument
    ```

## Align comments

Comments are not aligned by default. You can enable it by configuring ``align_comments``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select AlignTestCasesSection -c AlignTestCasesSection.align_comments=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "AlignTestCasesSection"
    ]
    configure = [
        "AlignTestCasesSection.align_comments=True"
    ]
    ```

It is especially useful if you want to use comments to name the aligned columns. For example:

```robotframework
*** Test Cases ***
Testing Random List
    [Template]    Validate Random List Selection
    # collection          nbr items
    ${SIMPLE LIST}        2             # first test
    ${MIXED LIST}         3             # second test
    ${NESTED LIST}        4             # third test
```

## Align settings separately

Settings are aligned together with the rest of the code in the keyword. You can configure it to be aligned separately.
It allows you to use different widths of the columns for settings (if ``alignment_type`` is set to ``auto``).
You can enable it by configuring ``align_settings_separately``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select AlignTestCasesSection -c AlignTestCasesSection.alignment_type=auto -c AlignTestCasesSection.align_settings_separately=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "AlignTestCasesSection"
    ]
    configure = [
        "AlignTestCasesSection.alignment_type=auto",
        "AlignTestCasesSection.align_settings_separately=True"
    ]
    ```

See example:

=== "Before"

    ```robotframework
    *** Test Cases ***
    Test Password Policy Minimum Length Input Errors
        [Timeout]   10 min
        [Tags]    tag    tag
        Log    ${argument_name}
        Perform Action And Wait For Result    ${argument_name}
    ```

=== "align_settings_separately=False (default)"

    ```robotframework
    *** Test Cases ***
    Test Password Policy Minimum Length Input Errors
        [Timeout]       10 min
        [Tags]          tag                 tag
        Log             ${argument_name}
        Perform Action And Wait For Result          ${argument_name}
    ```

=== "align_settings_separately=True"

    ```robotframework
    *** Test Cases ***
    Test Password Policy Minimum Length Input Errors
        [Timeout]       10 min
        [Tags]          tag         tag
        Log     ${argument_name}
        Perform Action And Wait     ${argument_name}
    ```

## Skip formatting

It is possible to use the following arguments to skip formatting of the code:

- [skip option](../skip_formatting.md#skip-option)
- [skip keyword call](../skip_formatting.md#skip-keyword-call)
- [skip keyword call pattern](../skip_formatting.md#skip-the-keyword-call-pattern)

It is highly recommended to use one of the ``skip`` options if you wish to use the alignment but you have part of the code
that looks better with manual alignment. It is also possible to use [disablers](../../configuration/disablers.md) but ``skip`` option
makes it easier to skip all instances of a given type of the code.
