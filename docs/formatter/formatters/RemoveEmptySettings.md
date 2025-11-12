# RemoveEmptySettings

Remove empty settings.

{{ configure_hint("RemoveEmptySettings") }}

=== "Before"

    ```robotframework
    *** Settings ***
    Documentation
    Suite Setup
    Metadata
    Metadata    doc=1
    Test Setup
    Test Teardown    Teardown Keyword
    Test Template
    Test Timeout
    Force Tags
    Default Tags
    Library
    Resource
    Variables

    *** Test Cases ***
    Test
        [Setup]
        [Template]    #  comment    and    comment
        [Tags]    tag
        Keyword
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Metadata    doc=1
    Test Teardown    Teardown Keyword

    *** Test Cases ***
    Test
        [Tags]    tag
        Keyword
    ```

You can configure which settings are affected by parameter ``work_mode``. Possible values:

- overwrite_ok (default) - does not remove settings that are overwriting suite settings (Test Setup,
  Test Teardown, Test Template, Test Timeout or Default Tags)
- always - works on every setting

Empty settings that are overwriting suite settings will be converted to be more explicit (given that there are
related suite settings present). You can disable that behavior by changing ``more_explicit``
parameter value to ``False``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure RemoveEmptySettings.more_explicit=False
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "RemoveEmptySettings.more_explicit=False"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Settings ***
    Test Timeout  1min
    Force Tags

    *** Test Case ***
    Test
        [Documentation]    Empty timeout means no timeout even when Test Timeout has been used.
        [Timeout]
        No timeout
    ```

=== "more_explicit=True (default)"

    ```robotframework
    *** Settings ***
    Test Timeout  1min

    *** Test Case ***
    Test
        [Documentation]    Empty timeout means no timeout even when Test Timeout has been used.
        [Timeout]    NONE
        No timeout
    ```

=== "more_explicit=False"

    ```robotframework
    *** Settings ***
    Test Timeout  1min

    *** Test Case ***
    Test
        [Documentation]    Empty timeout means no timeout even when Test Timeout has been used.
        [Timeout]
        No timeout
    ```

If you want to remove all empty settings even if they are overwriting suite settings (like in above example) then
set ``work_mode`` to ``always``:

=== ":octicons-command-palette-24: cli"

    ```bash
    robocop format --configure RemoveEmptySettings.work_mode=always
    ```

=== ":material-file-cog-outline: toml"

    ```toml
    [tool.robocop.format]
    configure = [
        "RemoveEmptySettings.work_mode=always"
    ]
    ```

will result in:

=== "Before"

    ```robotframework
    *** Settings ***
    Test Timeout  1min
    Force Tags

    *** Test Case ***
    Test
        [Documentation]    Empty timeout means no timeout even when Test Timeout has been used.
        [Timeout]
        No timeout
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Test Timeout  1min

    *** Test Case ***
    Test
        [Documentation]    Empty timeout means no timeout even when Test Timeout has been used.
        No timeout
    ```
