# OrderSettings

Order settings like ``[Arguments]``, ``[Setup]``, ``[Tags]`` inside Keywords and Test Cases.

{{ configure_hint("OrderSettings") }}

Test case settings ``[Documentation]``, ``[Tags]``, ``[Template]``, ``[Timeout]``, ``[Setup]`` are put before test case
body and ``[Teardown]`` is moved to the end of a test case.

Keyword settings ``[Documentation]``, ``[Tags]``, ``[Timeout]``, ``[Arguments]``, ``[Setup]`` are put before keyword
body and settings like ``[Teardown]``, ``[Return]`` are moved to the end of keyword.

=== "Before"

    ```robotframework
    *** Test Cases ***
    Test
        [Setup]    Setup
        [Teardown]    Teardown
        [Documentation]    Test documentation.
        [Tags]    tags
        [Template]    Template
        [Timeout]    60 min
        Test Step


    *** Keywords ***
    Keyword
        [Teardown]    Keyword
        [Return]    ${value}
        [Arguments]    ${arg}
        [Documentation]    this is
        ...    doc
        [Tags]    sanity
        Pass
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    Test
        [Documentation]    Test documentation.
        [Tags]    tags
        [Template]    Template
        [Timeout]    60 min
        [Setup]    Setup
        Test Step
        [Teardown]    Teardown


    *** Keywords ***
    Keyword
        [Documentation]    this is
        ...    doc
        [Tags]    sanity
        [Arguments]    ${arg}
        PassAh
        [Teardown]    Keyword
        [Return]    ${value}
    ```

## Configure the order of the settings

The default order can be changed using the following parameters:

- ``keyword_before = documentation,tags,arguments,timeout,setup``
- ``keyword_after = teardown,return``
- ``test_before = documentation,tags,template,timeout,setup``
- ``test_after = teardown``

For example:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure OrderSettings.test_before=setup,teardown -c OrderSettings.test_after=documentation,tags
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "OrderSettings.test_before=setup,teardown",
        "OrderSettings.test_after=documentation,tags"
    ]
    ```

It is not required to overwrite all orders. For example, configuring only ``test_before`` and ``test_after`` keeps
keyword order as default.

=== "Before"

    ```robotframework
    *** Test Cases ***
    Test case 1
        [Documentation]    this is
        ...      doc
        [Teardown]    Teardown
        Keyword1
        [Tags]
        ...    tag
        [Setup]    Setup  # comment
        Keyword2


    *** Keywords ***
    Keyword
        [Documentation]    this is
        ...    doc
        [Tags]    sanity
        [Arguments]    ${arg}
        Pass
        [Teardown]    Keyword
    ```

=== "After"

    ```robotframework
    *** Test Cases ***
    Test case 1
        [Setup]    Setup  # comment
        [Teardown]    Teardown
        Keyword1
        Keyword2
        [Documentation]    this is
        ...    doc
        [Tags]
        ...    tag


    *** Keywords ***
    Keyword
        [Documentation]    this is
        ...    doc
        [Tags]    sanity
        [Arguments]    ${arg}
        Pass
        [Teardown]    Keyword
    ```

Not all settings names need to be passed to a given parameter. Missing setting names are not ordered. Example:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format -c OrderSettings.keyword_before= -c OrderSettings.keyword_after=
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "OrderSettings.keyword_before=",
        "OrderSettings.keyword_after="
    ]
    ```

It will order only test cases because all setting names for keywords are missing.

Setting name cannot be present in both before/after parts. For example ``keyword_before=tags`` ``keyword_after=tags``
configuration is invalid because ``tags`` cannot be ordered both before and after. It is important if you are
overwriting the default order, since in most cases you need to overwrite both before/after parts.
This configuration is invalid because teardown is by default part of the ``test_after``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format -c OrderSettings.keyword_before= -c OrderSettings.keyword_after=
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "OrderSettings.keyword_before=",
        "OrderSettings.keyword_after="
    ]
    ```

We need to overwrite both orders:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format -c OrderSettings.test_before=teardown -c OrderSettings.test_after=
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "OrderSettings.test_before=teardown",
        "OrderSettings.test_after="
    ]
    ```

## Settings comments

Comments next to settings will be moved together.

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        # comment about step
        Step
        # comment about arguments
        [Arguments]    ${arg}
    ```

=== "After"

    ```robotframework
    *** Keywords ***
    Keyword
        # comment about arguments
        [Arguments]    ${arg}
        # comment about step
        Step
    ```
