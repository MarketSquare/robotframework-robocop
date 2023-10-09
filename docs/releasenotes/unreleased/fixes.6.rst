inline-if-can-be-used should not suggest using invalid syntax (#951)
-----------------------------------------------------------------------------------

I0916 ``inline-if-can-be-used`` recommended to convert short `IF` to inline `IF` even if it was not possible without
adding additional code. See example:

```
*** Keywords ***
Set Variable On Flag Value
    [Arguments]    ${flag}
    # ${var} value will be set to `1` only if ${flag} is True
    IF    $flag
        ${var}    Set Variable    1
    END

    # ${var} will be `1` if ${flag} is True and `None` otherwise - which may be unexpected
    ${var}    IF    $flag    Set Variable    1

    # previous example 'fixed' to work the same as IF block
    ${var}    IF    $flag    Set Variable    1    ELSE    Set Variable    ${var}
```

Because of that ``inline-if-can-be-used`` will no longer recommend to convert `IF` blocks with assignments to `Inline IF`.
