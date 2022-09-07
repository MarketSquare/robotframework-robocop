*** Variables ***
${var}
... val
 .... val
value

&{dict}    1

@{variable}    a
...    b
....   c
...
...d

   ${var5}  2

*** Keywords ***
    [Arguments]     1
    value    My Keyword
    My Keyword     ${var}    ${value}
