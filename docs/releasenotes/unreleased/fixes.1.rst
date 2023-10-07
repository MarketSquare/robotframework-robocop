${_} should be ignored by duplicated-assigned-var-name (#954)
-------------------------------------------------------------

`duplicated-assigned-var-name` now allows to use `${_}` as replacement for duplicated assignments:

```
${_}  ${middle}  ${_}    Unpack Variable    ${variable}
```
