# SplitTooLongLine

Split too long lines.

{{ configure_hint("SplitTooLongLine") }}

If a line exceeds the given length limit (120 by default), it will be split:

=== "Before"

    ```robotframework
    *** Variables ***
    @{LIST}    value    value2    value3  # let's assume that value2 is at 120 char

    *** Keywords ***
    Keyword
        Keyword With Longer Name    ${arg1}    ${arg2}    ${arg3}  # let's assume that arg2 is at 120 char
    ```

=== "After"

    ```robotframework
    *** Variables ***
    # let's assume that value2 is at 120 char
    @{LIST}
    ...    value
    ...    value2
    ...    value3

    *** Keywords ***
    Keyword
        # let's assume that arg2 is at 120 char
        Keyword With Longer Name
        ...    ${arg1}
        ...    ${arg2}
        ...    ${arg3}
    ```

???+ example "Missing functionality"

    ``SplitTooLongLine`` does not support splitting all Robot Framework types. Currently it will only work on too
    long keyword calls, variables and selected settings (tags and arguments). Missing types will be covered in the future
    updates.

## Allowed line length

Allowed line length is configurable using global parameter ``--line-length``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --line-length 140
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    line-length = 140
    ```

Or using dedicated for this formatter parameter ``line_length``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure SplitTooLongLine.line_length=140
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "SplitTooLongLine.line_length=140"
    ]
    ```

## Split argument on every line

Using ``split_on_every_arg`` flag (``True`` by default), you can force the formatter to fill keyword arguments
in one line until character limit:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure SplitTooLongLine.split_on_every_arg=False
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "SplitTooLongLine.split_on_every_arg=False"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        Keyword With Longer Name    ${arg1}    ${arg2}    ${arg3}  # let's assume that arg2 is at 120 char
    ```

=== "After"

    ```robotframework
    *** Keywords ***
    Keyword
        # let's assume that arg2 is at 120 char
        Keyword With Longer Name    ${arg1}
        ...    ${arg2}    ${arg3}
    ```

## Split values on every line

Using ``split_on_every_value`` flag (``True`` by default), you can force the formatter to fill values in one line
until character limit:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure SplitTooLongLine.split_on_every_value=False
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "SplitTooLongLine.split_on_every_value=False"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Variables ***
    # let's assume character limit is at age=12
    &{USER_PROFILE}    name=John Doe    age=12     hobby=coding
    ```

=== "After"

    ```robotframework
    *** Variables ***
    # let's assume character limit is at age=12
    &{USER_PROFILE}    name=John Doe    age=12
    ...    hobby=coding
    ```

## Split settings arguments on every line

Using ``split_on_every_setting_arg`` flag (``True`` by default), you can force the formatter to fill settings arguments
in one line until character limit:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure SplitTooLongLine.split_on_every_setting_arg=False
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "SplitTooLongLine.split_on_every_setting_arg=False"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Keywords ***
    Arguments
        [Arguments]    ${short}    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
        Step
    ```

=== "After (default)"

    ```robotframework
    *** Keywords ***
    Arguments
        [Arguments]
        ...    ${short}
        ...    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
        ...    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
        Step
    ```

=== "After (split_on_every_setting_arg set to False)"

    ```robotframework
    *** Keywords ***
    Arguments
        [Arguments]    ${short}    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
        ...    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
        Step
    ```

## Assignments

Assignments will be split to multi lines if they don't fit together with the Keyword in one line:

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        ${first_assignment}    ${second_assignment}    Some Lengthy Keyword So That This Line Is Too Long    ${arg1}    ${arg2}

        ${first_assignment}    ${second_assignment}    ${third_assignment}    Some Lengthy Keyword So That This Line Is Too Long And Bit Over    ${arg1}    ${arg2}
    ```

=== "After"

    ```robotframework
    *** Keywords ***
    Keyword
        ${first_assignment}    ${second_assignment}    Some Lengthy Keyword So That This Line Is Too Long
        ...    ${arg1}
        ...    ${arg2}

        ${first_assignment}
        ...    ${second_assignment}
        ...    ${third_assignment}
        ...    Some Lengthy Keyword So That This Line Is Too Long And Bit Over
        ...    ${arg1}
        ...    ${arg2}
    ```

## Single values

By default, single values (``${variable}    value``) are not split. You can configure ``SplitTooLine`` formatter
to split on single too long values using ``split_single_value`` option:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure SplitTooLongLine.split_single_value=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "SplitTooLongLine.split_single_value=True"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Variables ***
    &{USER_PROFILE}                   name=John Doe                            age=12                            hobby=coding
    ${SHORT_VALUE}    value
    ${SINGLE_HEADER}    veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery
    ```

=== "After (default)"

    ```robotframework
    *** Variables ***
    &{USER_PROFILE}
    ...    name=John Doe
    ...    age=12
    ...    hobby=coding
    ${SHORT_VALUE}    value
    ${SINGLE_HEADER}    veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery
    ```

=== "After (split_single_value = True)"

    ```robotframework
    *** Variables ***
    &{USER_PROFILE}
    ...    name=John Doe
    ...    age=12
    ...    hobby=coding
    ${SHORT_VALUE}    value
    ${SINGLE_HEADER}
    ...    veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery
    ```

## Align a new line

It is possible to align a new line to the previous line when splitting too long line. This mode works only when we are
filling the line until line the length limit (with one of the ``split_on_every_arg``, ``split_on_every_value`` and
``split_on_every_setting_arg`` flags). To enable it, configure it using ``align_new_line``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure SplitTooLongLine.align_new_line=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "SplitTooLongLine.align_new_line=True"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        [Tags]    longertagname1    longertagname2    longertagname3
        Keyword With Longer Name    ${arg1}    ${arg2}    ${arg3}    # let's assume ${arg3} does not fit under limit
    ```

=== "After (align_new_line = False)"

    ```robotframework
    *** Keywords ***
    Keyword
        [Tags]    longertagname1    longertagname2
        ...    longertagname3
        Keyword With Longer Name    ${arg1}    ${arg2}
        ...    ${arg3}
    ```

=== "After (align_new_line = True)"

    ```robotframework
    *** Keywords ***
    Keyword
        [Tags]    longertagname1    longertagname2
        ...       longertagname3
        Keyword With Longer Name    ${arg1}    ${arg2}
        ...                         ${arg3}
    ```

## Ignore comments

To not count the length of the comment to line length, use [skip option](../skip_formatting.md#skip-option) option:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure SplitTooLongLine.skip_comments=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "SplitTooLongLine.skip_comments=True"
    ]
    ```

This allows to ignore lines that are longer than allowed length because of the added comment.

## Skip formatting

It is possible to use the following arguments to skip formatting of the code:

- [skip option](../skip_formatting.md#skip-option)
- [skip keyword call](../skip_formatting.md#skip-keyword-call)
- [skip keyword call pattern](../skip_formatting.md#skip-the-keyword-call-pattern)
- [skip sections](../skip_formatting.md#skip-sections)

It is also possible to use [disablers](../../configuration/disablers.md) but ``skip`` option makes it easier to skip
all instances of a given type of the code.
