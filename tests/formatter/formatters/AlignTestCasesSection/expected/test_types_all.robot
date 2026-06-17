*** Test Cases ***
Test case
    ${short}                Short Keyword           short arg
    ${other_val}            Short Keyword
    ...                     arg
    ...                     value

Testing Random List
    [Template]              Validate Random List Selection
    # collection            nbr items
    ${SIMPLE LIST}          2                       # first test
    ${MIXED LIST}           3                       # second test
    ${NESTED LIST}          4                       # third test
