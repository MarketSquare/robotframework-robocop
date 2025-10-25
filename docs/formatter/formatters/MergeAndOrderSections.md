# MergeAndOrderSections

Merge duplicated sections and order them.

{{ configure_hint("MergeAndOrderSections") }}

The default order is: Comments > Settings > Variables > Test Cases > Keywords.

=== "Before"

    ```robotframework
    # this is comment section
    *** Keywords ***
    Keyword
        No Operation

    *** Test Cases ***
    Test 1
        Log  1

    Test 2
        Log  2

    *** Settings ***
    Library  somelib.py
    Test Template    Template


    *** Keyword ***
    Keyword2
        Log  2
        FOR  ${i}  IN RANGE  10
            Log  ${i}
        END

    *** Test Cases ***
    Test 3
        Log  3


    *** Variables ***  this should be left  alone
    ${var}  1
    @{var2}  1
    ...  2


    *** settings***
    Task Timeout  4min

    Force Tags  sometag  othertag
    ```

=== "After"

    ```robotframework
    *** Comments ***

    # this is comment section
    *** Settings ***
    Library  somelib.py
    Test Template    Template


    Task Timeout  4min

    Force Tags  sometag  othertag
    *** Variables ***  this should be left  alone
    ${var}  1
    @{var2}  1
    ...  2


    *** Test Cases ***
    Test 1
        Log  1

    Test 2
        Log  2

    Test 3
        Log  3


    *** Keywords ***
    Keyword
        No Operation

    Keyword2
        Log  2
        FOR  ${i}  IN RANGE  10
            Log  ${i}
        END
    ```

## Custom order

You can change sorting order by configuring ``order`` parameter with the comma-separated list of section names (without
spaces):

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure MergeAndOrderSections.order=settings,keywords,variables,testcases,comments
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "MergeAndOrderSections.order=settings,keywords,variables,testcases,comments"
    ]
    ```

## Miscellaneous

Because merging and changing the order of sections can shuffle your empty lines it's greatly advised to always
run ``NormalizeNewLines`` formatter after this one. This is done by default, so this advice applies only if you're
running formatters separately.

If both ``*** Test Cases ***`` and ``*** Tasks ***`` are defined in one file they will be merged into one (header
name will be taken from the first encountered section).

Any data before the first section is treated as comment in Robot Framework. This formatter add ``*** Comments ***``
section for such lines:

=== "Before"

    ```robotframework
    i am comment
    # robocop: off
    *** Settings ***
    ```

=== "After"

    ```robotframework
    *** Comments ***
    i am comment
    # robocop: off
    *** Settings ***
    ```

You can disable this behaviour by setting ``create_comment_section`` to False:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure MergeAndOrderSections.create_comment_section=False
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "MergeAndOrderSections.create_comment_section=False"
    ]
    ```
