*** Settings ***
Suite Setup    Run Keywords
...    No Operation
# ...    No Operation
Suite Teardown    Run Keywords    No Operation    No Operation   # comment
Test Setup    Run Keywords
# ...    No Operation
...    No Operation


*** Keywords ***
Comments
    Run Keyword  # comment1  comment2
    ...    Run Keyword If    ${True}    # comment 3
    ...        Keyword    # comment 4
    ...        ${arg}  # comment 5
    ...   ELSE  # comment 6
    ...      Keyword  # comment 7

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
