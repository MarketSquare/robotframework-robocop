New rule arguments-per-continuation-line (#1000)
------------------------------------------------

Added new I0532 ``arguments-per-continuation-line`` rule.

If the keywords ``[Arguments]`` are split into multiple lines, it is recommended to put only one argument per
every line.

Example of rule violation::

    *** Keywords ***
    Keyword With Multiple Arguments
    [Arguments]    ${first_arg
    ...    ${second_arg}    ${third_arg}=default
