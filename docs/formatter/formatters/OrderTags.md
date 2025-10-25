# OrderTags

Order tags in a case-insensitive way in ascending order.

{{ enable_hint("OrderTags") }}

This relates to tags in Test Cases, Keywords, Force Tags and Default Tags.

=== "Before"

    ```robotframework
    *** Settings ***
    Documentation       OrderTags acceptance tests
    Force Tags      forced_tag_1    forced_tag_aa     forced_tag_2    forced_tag_Ab    forced_tag_Bb    forced_tag_ba
    Default Tags    default_tag_1    default_tag_aa    default_tag_2    default_tag_Ab    default_tag_Bb    default_tag_ba

    *** Test Cases ***
    Tags Upper Lower
        [Tags]    ba    Ab    Bb    Ca    Cb    aa
        My Keyword

    *** Keywords ***
    My Keyword
        [Tags]    ba    Ab    Bb    Ca    Cb    aa
        No Operation
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Documentation       OrderTags acceptance tests
    Force Tags          forced_tag_1    forced_tag_2    forced_tag_aa    forced_tag_Ab    forced_tag_ba    forced_tag_Bb
    Default Tags        default_tag_1    default_tag_2    default_tag_aa    default_tag_Ab    default_tag_ba    default_tag_Bb

    *** Test Cases ***
    Tags Upper Lower
        [Tags]    aa    Ab    ba    Bb    Ca    Cb
        My Keyword

    *** Keywords ***
    My Keyword
        [Tags]    aa    Ab    ba    Bb    Ca    Cb
        No Operation
    ```

Using the same example with ``reverse=True`` param we will get tags in descending order:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select OrderTags --configure OrderTags.reverse=True
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "OrderTags"
    ]
    configure = [
        "OrderTags.reverse=True"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Test Cases ***
    Tags Upper Lower
        [Tags]    ba    Ab    Bb    Ca    Cb    aa
        My Keyword
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    Tags Upper Lower
        [Tags]    Cb    Ca    Bb    ba    Ab    aa
        My Keyword
    ```

Tags can be also ordered in a case-sensitive way:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select OrderTags --configure OrderTags.case_sensitive=True -c OrderTags.reverse=False
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "OrderTags"
    ]
    configure = [
        "OrderTags.case_sensitive=True",
        "OrderTags.reverse=False"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Test Cases ***
    Tags Upper Lower
        [Tags]    ba    Ab    Bb    Ca    Cb    aa
        My Keyword
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    Tags Upper Lower
        [Tags]    Ab    Bb    Ca    Cb    aa    ba
        My Keyword
    ```

Force Tags and Default Tags ordering can be disabled like this:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --select OrderTags --configure OrderTags.default_tags=False -c OrderTags.force_tags=False
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    select = [
        "OrderTags"
    ]
    configure = [
        "OrderTags.default_tags=False",
        "OrderTags.force_tags=False"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Settings ***
    Documentation       OrderTags acceptance tests
    Force Tags      forced_tag_1    forced_tag_aa     forced_tag_2    forced_tag_Ab    forced_tag_Bb    forced_tag_ba
    Default Tags    default_tag_1    default_tag_aa    default_tag_2    default_tag_Ab    default_tag_Bb    default_tag_ba

    *** Test Cases ***
    Tags Upper Lower
        [Tags]    ba    Ab    Bb    Ca    Cb    aa
        My Keyword
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Documentation       OrderTags acceptance tests
    Force Tags      forced_tag_1    forced_tag_aa     forced_tag_2    forced_tag_Ab    forced_tag_Bb    forced_tag_ba
    Default Tags    default_tag_1    default_tag_aa    default_tag_2    default_tag_Ab    default_tag_Bb    default_tag_ba

    *** Test Cases ***
    Tags Upper Lower
        [Tags]    aa    Ab    ba    Bb    Ca    Cb
        My Keyword
    ```
