Non variables detected as variable by variable rules (#982)
-----------------------------------------------------------

String literals will no longer be detected as variables by variables rules such as W0919 ``unused-argument``
or I0920 ``unused-variable``:

```
Used In String Literal
    [Arguments]    ${used}    ${unused}
    Log  ${used} unused  # unused is just a string, not a variable
```
