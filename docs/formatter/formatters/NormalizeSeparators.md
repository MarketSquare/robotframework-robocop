# NormalizeSeparators

Normalize separators and indents.

{{ configure_hint("NormalizeSeparators") }}

All separators (pipes included) are converted to fixed length of 4 spaces (configurable via global option
``--space-count``). To separately configure the indentation, use ``--indent`` global option.

???+ note

    There are formatters that also affect separator lengths - for example ``AlignSettingsSection``. ``NormalizeSeparators``
    is used as a base and then potentially overwritten by behaviours of other formatters. If you only want to have fixed
    separator lengths (without aligning) then only run this formatter without running the others.

=== "Before"

    ```robotframework
    *** Settings ***
    Library  library.py  WITH NAME          alias

    Force Tags           tag
    ...   tag

    Documentation  doc
    ...      multi
    ...  line

    *** Test Cases ***
    Test case
      [Setup]  Keyword
       Keyword  with  arg
       ...  and  multi  lines
         [Teardown]          Keyword

    Test case with structures
        FOR  ${variable}  IN  1  2
        Keyword
         IF  ${condition}
           Log  ${stuff}  console=True
      END
       END
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Library    library.py    WITH NAME    alias

    Force Tags    tag
    ...    tag

    Documentation    doc
    ...    multi
    ...    line

    *** Test Cases ***
    Test case
        [Setup]    Keyword
        Keyword    with    arg
        ...    and    multi    lines
        [Teardown]    Keyword

    Test case with structures
        FOR    ${variable}    IN    1    2
            Keyword
            IF    ${condition}
                Log    ${stuff}    console=True
            END
        END
    ```

## Configure separator

By configuring a global option ``space-count``, you can change the default separator length:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --space-count 8
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    space-count = 8
    ```

will result in:

=== "Before"

    ```robotframework
    *** Settings ***
    Library  library.py  WITH NAME          alias

    Force Tags           tag
    ...   tag
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Library        library.py        WITH NAME        alias

    Force Tags        tag
    ...        tag
    ```

## Indentation

By default, indentation is the same as ``space-count`` value (default ``4`` spaces). To configure it, use ``--indent``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --indent 4
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    indent = 4
    ```

Combine it with ``space-count`` to set whitespace separately for indent and separators:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --indent 4 --space-count 2
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    indent = 4
    space-count = 2
    ```

this configuration will result in:

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
      FOR     ${var}  IN RANGE     10
        Keyword With  ${var}
      END
    ```

=== "After"

    ```robotframework
    *** Keywords ***
    Keyword
        FOR  ${var}  IN RANGE  10
            Keyword With  ${var}
        END
    ```

## Flatten multi line statements

By default ``NormalizeSeparators`` only updates the separators and leave any multi line intact. It is possible to
flatten multi line statements into single line using ``flatten_lines`` option:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format -c NormalizeSeparators.flatten_lines=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "NormalizeSeparators.flatten_lines=True"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        Keyword Call    1  2
          ...    1  # comment
        ...    2          3
    ```

=== "After - default (flatten_lines = False)"

    ```robotframework
    *** Keywords ***
    Keyword
        Keyword Call    1    2
        ...    1    # comment
        ...    2    3
    ```

=== "After (flatten_lines = True)"

    ```robotframework
    *** Keywords ***
    Keyword
        Keyword Call    1    2    1    2    3  # comment
    ```

## Align new lines

It is possible to align new lines to the first line. This alignment will be overwritten if you have formatters affecting
alignment enabled, such as:

- AlignKeywordsSection
- AlignSettingsSection
- AlignTemplatedTestCases
- AlignTestCasesSection
- AlignVariablesSection

You can enable it using ``align_new_line`` parameter:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure NormalizeSeparators.align_new_line=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "NormalizeSeparators.align_new_line=True"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Test Cases ***
    Test
        [Tags]    tag
        ...  tag2

    *** Keywords ***
    Keyword
        [Arguments]    ${argument1}
        ...    ${argument2} ${argument3}
        Keyword Call    argument
        ...  arg2
        ...    arg3
    ```

=== "After - default (align_new_line=False)"

    ```robotframework
    *** Test Cases ***
    Test
        [Tags]    tag
        ...    tag2

    *** Keywords ***
    Keyword
        [Arguments]    ${argument1}
        ...    ${argument2}   ${argument3}
        Keyword Call    argument
        ...    arg2
        ...    arg3
    ```

=== "After (align_new_line=True)"

    ```robotframework
    *** Test Cases ***
    Test
        [Tags]    tag
        ...       tag2

    *** Keywords ***
    Keyword
        [Arguments]    ${argument1}
        ...            ${argument2}   ${argument3}
        Keyword Call    argument
        ...             arg2
        ...             arg3
    ```

## Skip formatting

It is possible to use the following arguments to skip formatting of the code:

- [skip option](../skip_formatting.md#skip-option)
- [skip keyword call](../skip_formatting.md#skip-keyword-call)
- [skip skip keyword call pattern](../skip_formatting.md#skip-the-keyword-call-pattern)
- [skip sections](../skip_formatting.md#skip-sections)

Documentation is formatted by default. To disable formatting the separators inside documentation, and to only format
indentation, set ``skip_documentation`` to ``True``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure NormalizeSeparators.skip_documentation=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "NormalizeSeparators.skip_documentation=True"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    TEST_TC
        [Argument]    ${a}    ${long_arg}
        [Documentation]     Test Doc.
        ...
        ...    Arguments:
        ...    a:               Argument A
        ...    long_arg:        Argument long_arg.
       Test Case Body
    ```

=== "skip_documentation=False (default)"

    ```robotframework
    TEST_TC
        [Argument]    ${a}    ${long_arg}
        [Documentation]     Test Doc.
        ...
        ...    Arguments:
        ...    a:    Argument A
        ...    long_arg:    Argument long_arg.
       Test Case Body
    ```

=== "skip_documentation=True"

    ```robotframework
    TEST_TC
        [Argument]    ${a}    ${long_arg}
        [Documentation]     Test Doc.
        ...
        ...    Arguments:
        ...    a:               Argument A
        ...    long_arg:        Argument long_arg.
       Test Case Body
    ```

It is also possible to use [disablers](../../configuration/disablers.md) but ``skip`` option makes it easier to skip all instances of a given type
of the code.
