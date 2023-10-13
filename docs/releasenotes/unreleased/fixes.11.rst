Variables with attribute access detected as unused (#971)
---------------------------------------------------------

Arguments and variables could be reported as unused with W0919 ``unused-argument`` or I0920 ``unused-variable``
if they were used with attribute access:

```
*** Keywords ***
Use Item With Attribute
    ${item}    Prepare Item
    Log    ${item.x}

Update Item With Attribute
    ${item}    Get Item
    ${item.x}    Set Variable    abc  # overwriting attribute should also count as using the variable

Use Item With Method
    ${string}    Set Variable    string
    ${lower_string}    Set Variable    ${string.lower()}
    Log    ${lower_string}
```

It should now be fixed. However our variable with attributes handling will be soon refactored to avoid similar cases
in the future - please report any false positive errors you may encounter.
