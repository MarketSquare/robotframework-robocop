# ReplaceReturns

Replace return statements (such as ``[Return]`` setting or ``Return From Keyword`` keyword) with new ``RETURN`` statement.

???+ note
    Required Robot Framework version: >=5.0

{{ configure_hint("ReplaceReturns") }}

This formatter replace ``[Return]`` statement with ``RETURN``:

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        Sub Keyword
        [Return]    ${value}
    ```

=== "After"

    ```robotframework
    *** Keywords ***
    Keyword
        Sub Keyword
        RETURN    ${value}
    ```

It also does replace ``Return From Keyword`` and ``Return From Keyword If``:

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        Return From Keyword If    $condition    ${value}
        Sub Keyword
        Return From Keyword    ${other_value}
    ```

=== "After"

    ```robotframework
    *** Keywords ***
    Keyword
        IF    $condition
            RETURN    ${value}
        END
        Sub Keyword
        RETURN    ${other_value}
    ```
