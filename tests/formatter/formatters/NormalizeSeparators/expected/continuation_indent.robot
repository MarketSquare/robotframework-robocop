*** Settings ***
Force Tags  value  value
...    value  value


*** Variables ***
@{LIST}  1
...    2
...    3  4  5

*** Keywords ***
Keyword
    [Arguments]  ${argument1}
    ...    ${argument2}  ${argument3}
    Keyword Call  1  2
    ...    1
    ...    2  3
    FOR  ${var}  IN  1  2
    ...    1  2
        Keyword Call  1  2
        ...    1  # comment
        ...    2  3
    END
    A
    ...    arg
    B  arg
    ...    arg2

Documentation
    [Documentation]  FAIL  Several failures occurred:\n\n
    ...    1) Keyword 'BuiltIn.Should Be Equal' expected 2 to 8 arguments, got 1.\n\n
    ...    2) Invalid argument specification: Invalid argument syntax '${arg'.\n\n
    ...    3) Keyword 'Some Return Value' expected 2 arguments, got 3.\n\n
    ...    4) No keyword with name 'Yet another non-existing keyword' found.\n\n
    ...    5) No keyword with name 'Does not exist' found.
