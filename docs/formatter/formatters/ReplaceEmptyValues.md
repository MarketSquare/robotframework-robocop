# ReplaceEmptyValues

Replace empty values with ``${EMPTY}`` variable.

{{ configure_hint("ReplaceEmptyValues") }}


Empty variables, lists or elements in the list can be defined in a way that omits the value.
To be more explicit, this formatter replace such values with ``${EMPTY}`` variables:

=== "Before"

    ```robotframework
    *** Variables ***
    ${EMPTY_VALUE}
    @{EMPTY_LIST}
    &{EMPTY_DICT}
    @{LIST_WITH_EMPTY}
    ...    value
    ...
    ...    value3
    ```

=== "After"

    ```robotframework
    *** Variables ***
    ${EMPTY_VALUE}    ${EMPTY}
    @{EMPTY_LIST}     @{EMPTY}
    &{EMPTY_DICT}     &{EMPTY}
    @{LIST_WITH_EMPTY}
    ...    value
    ...    ${EMPTY}
    ...    value3
    ```

## Skip formatting

It is possible to use the following arguments to skip formatting of the code:

- [skip sections](../skip_formatting.md#skip-sections)
