*** Settings ***
Suite Setup    Run Keywords
...    No Operation
# ...    No Operation
# comment
Suite Teardown    Run Keywords
...    No Operation
...    No Operation
Test Setup    Run Keywords
# ...    No Operation
...    No Operation


*** Keywords ***
Comments
    # comment1  comment2
    # comment 3
    # comment 4
    # comment 5
    # comment 6
    # comment 7
    Run Keyword
    ...    Run Keyword If    ${True}
    ...        Keyword    ${arg}
    ...    ELSE
    ...        Keyword

Golden Keywords
    [Test Setup]    Run Keywords
    ...    No Operation
    #    No Operation
    ...    No Operation

    Run Keywords
    ...    No Operation
    # ...    No Operation
    ...    No Operation

    Run Keywords
    ...    No Operation
    ...    No Operation  # comment about this keyword call
