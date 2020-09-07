*** Settings ***
Documentation  This is suite doc

*** Test Cases ***
This is test
    [Documentation]  Test case doc
    Log  1
    FOR  ${index}  IN RANGE  0  10
        This Is Keyword
    END

*** Keywords ***
This Is Keyword
    [Documentation]  Keyword doc
    FOR  ${elem}  IN  elem1  elem2  elem3
    ...  elem4
        Log  ${elem}  # this is valid comment TODO:
        not capitalized Keyword
    END
    [Return]
    Return From_keyword
    Log  smth