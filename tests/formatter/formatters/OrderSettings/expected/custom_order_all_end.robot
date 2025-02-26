*** Test Cases ***
Test case 1
    Keyword
    Keyword
    [Documentation]  this is
    ...    doc
    [Tags]
    ...  tag
    [Setup]  Setup  # comment
    [Teardown]  Teardown

Test case 2
    Keyword
    [Timeout]  timeout2  # this is error because it is duplicate
    [Template]  Template
    [Timeout]  timeout

Test case with comment at the end
    [Teardown]  Keyword
    #  comment

# comment

Test case 3
    Golden Keyword

Test case 4
   Keyword1
   # comment1
   Keyword2
   # comment2
   Keyword3
   [Teardown]  teardown

Test case 5  # comment1
   Keyword1
   # comment2
   Keyword2
   # comment3
   Keyword3
   [Documentation]  this is
   [Teardown]  teardown

*** Keywords ***
Keyword
    Keyword
    No Operation
    IF  ${condition}
        Log  ${stuff}
    END
    FOR  ${var}  IN  1  2
        Log  ${var}
    END
    Pass
    [Documentation]  this is
    ...    doc
    [Tags]  sanity
    [Arguments]  ${arg}
    [Teardown]  Keyword
    [Setup]  Setup
    [Return]  ${value}

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
    Keyword
    [Return]  stuff
    # I want to be here

Comment on the same line  # comment
    [Documentation]  this is
    ...    doc

# what will happen with me?
