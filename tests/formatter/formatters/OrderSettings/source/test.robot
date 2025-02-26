*** Test Cases ***
Test case 1
    [Documentation]  this is
    ...    doc
    [Teardown]  Teardown
    Keyword
    [Tags]
    ...  tag
    [Setup]  Setup  # comment
    Keyword

Test case 2
    [Template]  Template
    Keyword
    [Timeout]  timeout
    [Timeout]  timeout2  # this is error because it is duplicate

Test case with comment at the end
    [Teardown]  Keyword
    #  comment

# comment

Test case 3
    Golden Keyword

Test case 4
   [Teardown]  teardown
   Keyword1
   # comment1
   Keyword2
   # comment2
   Keyword3

Test case 5  # comment1
   [Teardown]  teardown
   [Documentation]  this is
   Keyword1
   # comment2
   Keyword2
   # comment3
   Keyword3

*** Keywords ***
Keyword
    [Teardown]  Keyword
    [Return]  ${value}
    [Arguments]  ${arg}
    [Documentation]  this is
    ...    doc
    [Tags]  sanity
    Keyword
    No Operation
    IF  ${condition}
        Log  ${stuff}
    END
    FOR  ${var}  IN  1  2
        Log  ${var}
    END
    Pass
    [Setup]  Setup

Another Keyword ${var}
    No Operation
    [Timeout]

Keyword With Comment
    Keyword
    [Return]  ${value}
    # I am comment

Keyword With Empty Line And Comment
    Keyword
    [Return]  ${value}

# I am comment in new line

Another Keyword
    No Operation
    # innocent comment

Comment Before setting
    Keyword
    # I want to be here
    [Return]    ${value}

Return first and comment last
    [Return]  stuff
    Keyword
    # I want to be here

Comment on the same line  # comment
    [Documentation]  this is
    ...    doc

# what will happen with me?
