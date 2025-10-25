# NormalizeSettingName

Normalize setting name.

{{ configure_hint("NormalizeSettingName") }}

Ensure that setting names are in a title case without leading or trailing whitespace.

=== "Before"

    ```robotframework
    *** Settings ***
    library    library.py
    test template    Template
    FORCE taGS    tag1

    *** Keywords ***
    Keyword
        [arguments]    ${arg}
        [TEARDOWN]   Teardown Keyword
    ```

=== "After"

    ```robotframework
    *** Settings ***
    Library    library.py
    Test Template    Template
    Force Tags    tag1

    *** Keywords ***
    Keyword
        [Arguments]    ${arg}
        [Teardown]   Teardown Keyword
    ```
