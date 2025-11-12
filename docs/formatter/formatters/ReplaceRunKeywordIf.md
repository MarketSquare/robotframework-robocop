# ReplaceRunKeywordIf

Replace ``Run Keyword If`` keyword calls with IF expressions.

{{ configure_hint("ReplaceRunKeywordIf") }}

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        Run Keyword If  ${condition}
        ...  Keyword  ${arg}
        ...  ELSE IF  ${condition2}  Keyword2
        ...  ELSE  Keyword3
    ```

=== "After"

    ```robotframework
    *** Keywords ***
    Keyword
        IF    ${condition}
            Keyword    ${arg}
        ELSE IF    ${condition2}
            Keyword2
        ELSE
            Keyword3
        END
    ```

Any return value will be applied to every ELSE/ELSE IF branch.

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        ${var}  Run Keyword If  ${condition}  Keyword  ELSE  Keyword2
    ```

=== "After"

    ```robotframework
    *** Keywords ***
    Keyword
        IF    ${condition}
            ${var}    Keyword
        ELSE
            ${var}    Keyword2
        END
    ```

Run Keywords inside Run Keyword If will be split into separate keywords.

=== "Before"

    ```robotframework
    *** Keywords ***
    Keyword
        Run Keyword If  ${condition}  Run Keywords  Keyword  ${arg}  AND  Keyword2
    ```

=== "After"

    ```robotframework
    *** Keywords ***
    Keyword
        IF    ${condition}
            Keyword    ${arg}
            Keyword2
        END
    ```

Run Keyword If that assigns values but does not provide a default branch will receive ELSE branch with Set Variable:

=== "Before"

    ```robotframework
        *** Keywords ***
        Keyword
            ${var}  Run Keyword If  ${condition}  Keyword
    ```

=== "After"

    ```robotframework
    *** Keywords ***
    Keyword
        IF    ${condition}
            ${var}    Keyword
        ELSE
            ${var}    Set Variable    ${None}
        END
    ```
