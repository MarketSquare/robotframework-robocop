*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More


*** Keywords ***
Keyword With Over Indented Line
    [Documentation]  this is doc
       No Operation
    Pass
    No Operation
    Fail

Keyword With Under Indented Line
    [Documentation]  this is doc
    No Operation
   Pass
    No Operation
    Fail

Keyword With Over Indented Setting
    [Documentation]  this is doc
     [Setup]  Keyword
       No Operation
    Pass
    No Operation
    Fail

Templated Test
    [Documentation]  doc
    [Template]  Some Template
                Over Indent
                ...  Same Here
    What Goes
     [Teardown]  Over Indented

Keyword With Multiline For Loop
    [Documentation]  Keyword doc
    [Tags]  tag
    FOR  ${elem}  IN  elem1  elem2  elem3
     ...  elem4
        Log  ${elem}  # this is valid comment
       Keyword

    END

Keyword With Under Indented For Loop Body
    FOR  ${elem}  IN  ${list}
   Log  stuff
    END

Keyword With Under Indented For Loop Body And Comment
    Keyword
    FOR    ${var}  IN   1  2
        Keyword
# invalid comment
    END
