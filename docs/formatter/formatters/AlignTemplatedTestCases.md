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

    *** Test Cases ***      baz         qux
    # some comment
    test1                   hi          hello
    test2 long test name    asdfasdf    asdsdfgsdfg
                            bar1        bar2
    ```

Any argument in the same line as the test case name will be used as a column header for the alignment:

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
    Test1     ARG1
              [Tags]              sanity
              [Documentation]     Validate Test1
    Test2     ARG2
              [Tags]              smoke
              [Documentation]     Validate Test2
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
    test1                         hi                            hello
    test2 long test name          asdfasdf                      asdsdfgsdfg
                                  bar1                          bar2
    ```
