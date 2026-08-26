# AlignTemplatedTestCases

Align suites with Test Template to columns.

For non-templated test cases use ``AlignTestCasesSection`` formatter. Test cases that are templated with
``[Template]`` setting should also use ``AlignTestCasesSection``.

{{ enable_hint("AlignTemplatedTestCases") }}

Examples:

=== "Before"

    ```robotframework
    *** Settings ***
    Test Template    Templated Keyword

    *** Test Cases ***    baz    qux
    # some comment
    test1    hi    hello
    test2 long test name    asdfasdf    asdsdfgsdfg
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Test Template    Templated Keyword

    *** Test Cases ***    baz         qux
    # some comment
    test1
                          hi          hello
    test2 long test name
                          asdfasdf    asdsdfgsdfg
    ```

By default (``args_with_test=split``) template arguments and settings are moved to their own line and the test case
names are ignored when calculating the column widths. See the [args_with_test](#control-arguments-placement-with-args_with_test)
section to keep arguments in the same line as the test case name.

With ``args_with_test=keep`` any argument in the same line as the test case name is kept there and used as a column
header for the alignment:

=== "Before"

    ```robotframework
    *** Settings ***
    Test Template    Dummy

    *** Test Cases ***
    Test1    ARG1
        [Tags]    sanity
        [Documentation]  Validate Test1
    Test2    ARG2
        [Tags]    smoke
        [Documentation]  Validate Test2
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Test Template    Dummy

    *** Test Cases ***
    Test1    ARG1
             [Tags]    sanity
             [Documentation]    Validate Test1
    Test2    ARG2
             [Tags]    smoke
             [Documentation]    Validate Test2
    ```

## Control arguments placement with args_with_test

Use the ``args_with_test`` parameter to control whether template arguments and settings stay in the same line as the
test case name. Possible values are ``split`` (default), ``split_on_settings`` and ``keep``:

- ``split`` always moves template arguments and settings to their own line, keeping only the test case name in the
  first line. Test case names are ignored when calculating the column widths (header names are still respected) and
  settings are not counted towards the column widths.
- ``split_on_settings`` moves template arguments and settings to their own line only if the test case contains any
  setting (such as ``[Tags]`` or ``[Documentation]``).
- ``keep`` keeps template arguments and settings in the same line as the test case name. When header names are present,
  the first body row is pulled up to the test case name line.

Test cases that contain block structures (``FOR``, ``IF``, ``TRY``, ``WHILE``) are always split, regardless of the
selected mode.

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select AlignTemplatedTestCases -c AlignTemplatedTestCases.args_with_test=keep
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "AlignTemplatedTestCases"
    ]
    configure = [
        "AlignTemplatedTestCases.args_with_test=keep"
    ]
    ```

=== "keep"

    ```robotframework
    *** Test Cases ***    baz       qux
    Without settings      arg1      arg2
    With setting          [Tags]    tag1
                          arg1      arg2
    ```

=== "split_on_settings"

    ```robotframework
    *** Test Cases ***    baz     qux
    Without settings      arg1    arg2
    With setting
        [Tags]    tag1
                          arg1    arg2
    ```

=== "split"

    ```robotframework
    *** Test Cases ***    baz     qux
    Without settings
                          arg1    arg2
    With setting
        [Tags]    tag1
                          arg1    arg2
    ```

## Align only the test case section with named headers

If you don't want to align test case section that does not contain header names then configure ``only_with_headers`` parameter:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select AlignTemplatedTestCases -c AlignTemplatedTestCases.only_with_headers=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "AlignTemplatedTestCases"
    ]
    configure = [
        "AlignTemplatedTestCases.only_with_headers=True"
    ]
    ```

## Fixed the width of the column

It's possible to set a fixed minimal width of a column. To configure it use ``min_width`` parameter:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select AlignTemplatedTestCases -c AlignTemplatedTestCases.min_width=30
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "AlignTemplatedTestCases"
    ]
    configure = [
        "AlignTemplatedTestCases.min_width=30"
    ]
    ```

This configuration respects ``up_to_column`` parameter which only aligns columns up to configured ``up_to_column``
column.

=== "Before"

    ```robotframework
    *** Test Cases ***    baz    qux
    # some comment
    test1    hi    hello
    test2 long test name    asdfasdf    asdsdfgsdfg
        bar1  bar2
    ```

=== "After"

    ```robotframework
    *** Test Cases ***            baz                           qux
    # some comment
    test1
                                  hi                            hello
    test2 long test name
                                  asdfasdf                      asdsdfgsdfg
                                  bar1                          bar2
    ```
