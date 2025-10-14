# AlignKeywordsSection

Align ``*** Keywords ***`` section to columns.

??? info "Enabling the formatter"

    AlignKeywordsSection is not included in default formatters. To enabled it, you need to call it with ``--select``
    explicitly:

    ```bash
    robocop format --select AlignKeywordsSection
    ```

    Or configure ``enabled`` parameter:

    ```bash
    robocop format --configure AlignKeywordsSection.enabled=True
    ```

Align keyword calls and settings into columns with predefined width. There are two possible alignment types
(configurable via ``alignment_type``):

- ``fixed`` (default): pad the tokens to the fixed width of the column
- ``auto``: pad the tokens to the width of the longest token in the column

The width of the column sets limit to the maximum width of the column. Default width is ``24``
(see :ref:`widths keywords` for information how to configure it).
With ``fixed`` alignment each column have fixed width (and tokens that does not fit
go into ``overflow`` state - see :ref:`overflow keywords`).

``auto`` alignment aligns tokens to the longest token in the column - the column width can be shorter than
configured width (but no longer).

See examples of the alignment types:

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        ${short}    Short Keyword    short arg
        ${other_val}    Short Keyword
        ...    arg
        ...    value
    ```

=== "fixed (default)"

    ```robotframework
    *** Keywords ***
    Keyword
        ${short}                Short Keyword           short arg
        ${other_val}            Short Keyword
        ...                     arg
        ...                     value
    ```

=== "auto"

    ```robotframework
    *** Keywords ***
    Keyword
        ${short}        Short Keyword       short arg
        ${other_val}    Short Keyword
        ...             arg
        ...             value
    ```

The ``auto`` alignment often leads to more compact code. But ``fixed`` setting offers more stability - adding new,
slightly longer variable or keyword call will not change alignment of the other lines.

.. _widths keywords:

## Widths

The column width is configurable via ``widths`` parameter. The default value is ``24``.
It's possible to configure width of the several columns (using comma separated list of integers):

```bash
robocop format -c AlignKeywordsSection.widths=20
```

```bash
robocop format -c AlignKeywordsSection.widths=10,10,24,30
```

The last width will be used for the remaining columns. In the previous example we configured widths for 4 columns.
The last width (``30``) will be used for 5th, 6th... and the following columns.

Use width ``0`` to disable column width limit. In ``auto`` alignment type it will always align whole column to the
longest token (no matter how long the token is).

.. _overflow keywords:

## Overflow

Tokens that do not fit in the column go into ``overflow`` state. There are several ways to deal with them (configurable
via ``handle_too_long`` parameter):

- ``overflow`` (default): align token to the next column
- ``compact_overflow``: try to fit the next token between current (overflowed) token and the next column
- ``ignore_rest``: ignore remaining tokens in the line
- ``ignore_line``: ignore whole line

See example (for ``fixed`` alignment type and default width ``24``):

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        # keyword call Looo.. does not fit default column width (24)
        ${assign}    Looooooooonger Keyword Name    ${argument}    last
        Short    Short    Short    Short
        Single
        Multi    ${arg}
        ...    ${arg}
    ```

=== "overflow (default)"

    ```robotframework
    *** Keywords ***
    Keyword
        # we are "overflowing" to the next column - taking 24 * 2 = 48 width
        ${assign}               Looooooooonger Keyword Name                     ${argument}             Short
        Short                   Short                   Short                   Short
        Single
        Multi                   ${arg}
        ...                     ${arg}
    ```

=== "compact_overflow"

    ```robotframework
    *** Keywords ***
    Keyword
        # ${argument} is fit between columns, and next argument ("last") is aligned correctly
        ${assign}               Looooooooonger Keyword Name    ${argument}      last
        Short                   Short                   Short                   Short
        Single
        Multi                   ${arg}
        ...                     ${arg}
    ```

=== "ignore_rest"

    ```robotframework
    *** Keywords ***
    Keyword
        # tokens after too long token are not aligned
        ${assign}               Looooooooonger Keyword Name    ${argument}    Short
        Short                   Short                   Short                   Short
        Single
        Multi                   ${arg}
        ...                     ${arg}
    ```

=== "ignore_line"

    ```robotframework
    *** Keywords ***
    Keyword
        # the whole line containing too long token is ignored
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
This behaviour helps in avoiding the situation, where ``compact_overflow`` misaligned whole line if most of the tokens
does not fit in the column.

Below example was run with config:

```bash
robocop format -c AlignKeywordsSection.enabled=True -c AlignKeywordsSection.handle_too_long=compact_overflow -c AlignKeywordsSection.widths=24,28,20
```

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        # compact overflow will be used as we only "misalign" two columns in a row
        LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO}    ${TILAUS}    ${OSTOTILAUS}    ${LÄHETYS}    ${TILAUSPVM}

        # more than two columns are misaligned - using "overflow" instead
        LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO_LONGER}    ${TILAUS_OCC}    ${OSTOTILAUS}    ${LÄHETYS}    ${TILAUSPVM}
    ```

=== "After"

    ```robotframework
    *** Keywords ***
    Keyword
        # compact overflow will be used as we only "misalign" two columns in a row
        LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO}    ${TILAUS}       ${OSTOTILAUS}       ${LÄHETYS}          ${TILAUSPVM}

        # more than two columns are misaligned - using "overflow" instead
        LäVa_VastaanottotapahtumatTarkista    ${VASTAANOTTO_LONGER}             ${TILAUS_OCC}       ${OSTOTILAUS}       ${LÄHETYS}          ${TILAUSPVM}
    ```

## Alignment of the indented blocks

Indented blocks (``FOR``, ``IF``, ``WHILE``, ``TRY..EXCEPT..``) are aligned independently.

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
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
    *** Keywords ***
    Keyword
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

``AlignKeywordsSection`` will split the lines if the lines after the alignment would exceed the limits set
in the :ref:`SplitTooLongLine` transformer.

???+ note

    Currently, only ``--configure SplitTooLongLine.split_on_every_arg=True`` mode is supported.

Using this configuration (``SplitTooLongLine`` is enabled by default):

```bash
robocop format -c AlignKeywordsSection.enabled=True -c AlignKeywordsSection.widths=14,24 --line-length 80
```

will result in the following transformation:

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        # fits now but it will not fit after the alignment
        Keyword    argument1    argument2    argument3    argument4

        # does not fit before the alignment
        Longer Keyword Name That Could Happen    argument value with sentence that goes over

        # fits, will not be split
        Keyword    argument
    ```

=== "After"

    ```robotframework
    *** Keywords ***
    Keyword
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

```bash
robocop format -c AlignKeywordsSection.align_comments=True
```

It is especially useful if you want to use comments to name the aligned columns. For example:

```robotframework
*** Keywords ***
Testing Random List
    [Documentation]    Validate Random List Selection
    # collection          nbr items
    ${SIMPLE LIST}        2             # first check
    ${MIXED LIST}         3             # second check
    ${NESTED LIST}        4             # third check
```

## Align settings separately

Settings are aligned together with the rest of the code in the keyword. You can configure it to be aligned separately.
It allows you to use different widths of the columns for settings (if ``alignment_type`` is set to ``auto``).
You can enable it by configuring ``align_settings_separately``:

=== ":octicons-command-palette-24:"

    ```bash
    robocop format --select AlignKeywordsSection -c AlignKeywordsSection.alignment_type=auto -c AlignKeywordsSection.align_settings_separately=True
    ```

=== ":material-file-cog-outline:"

    ```toml
    [tool.robocop.format]
    select = [
        "AlignKeywordsSection"
    ]
    configure = [
        "AlignKeywordsSection.alignment_type=auto",
        "AlignKeywordsSection.align_settings_separately=True"
    ]
    ```

Example:

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        [Arguments]   ${argument_name}
        [Tags]    tag    tag
        Log    ${argument_name}
        Perform Action And Wait For Result    ${argument_name}
    ```

=== "align_settings_separately=False (default)"

    ```robotframework
    *** Keywords ***
    Keyword
        [Tags]          tag
        [Arguments]     ${argument_name}
        Log             ${argument_name}
        Perform Action And Wait For Result              ${argument_name}
    ```

=== "align_settings_separately=True"

    ```robotframework
    *** Keywords ***
    Keyword
        [Tags]          tag
        [Arguments]     ${argument_name}
        Log     ${argument_name}
        Perform Action And Wait For Result              ${argument_name}
    ```

## Skip formatting

It is possible to use the following arguments to skip formatting of the code:

- :ref:`skip option`
- :ref:`skip keyword call`
- :ref:`skip keyword call pattern`

It is highly recommended to use one of the ``skip`` options if you wish to use alignment but you have part of the code
that looks better with manual alignment. It is also possible to use disablers (:ref:`disablers`) but ``skip`` option
makes it easier to skip all instances of given type of the code.
