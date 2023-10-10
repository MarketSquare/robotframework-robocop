variable-overwritten-before-usage should not be raised if overridden in an IF block (#950)
------------------------------------------------------------------------------------------

W0922 ``variable-overwritten-before-usage`` warns if the variable was overwritten before first use. It should now
ignore cases where the variable was initiated and then conditionally overriden in a IF block:

```
Conditionally Overriden Variable
    ${output}  Set Variable  default_value
    IF    os.path.isdir("/special_dir")
        ${output}  Set Variable  special_value  # it will not be reported from now on
    END
    RETURN    ${output}
```

Such cases could be also handled better by using `IF` with `ELSE` branch or `Set Variable If`. However, in more
complicated case this rule produced lot of additional unnecessary reports and this fix should help with it.
