*** Variables ***
${SHORT}  # first row is empty so all should be aligned to 2nd
...    value
...    value2

@{LIST}    value  # second row value is after variable name so it should be aligned with 1st
...    value
...    value2
${LONGER_VARIABLE}    value  # second row is before variable name so it should be aligned to 2nd
...    value2
...    value3