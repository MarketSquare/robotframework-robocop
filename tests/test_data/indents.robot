*** Settings ***
Documentation  This is suite doc
  Library  StatusLibrary


*** Variables ***
 ${var}  1
${var2}  2
 @{var3}  a
 ...      b
 ...      c
...      d
@{var4}  a
...      1
 ...     2

*** Test Cases ***
This is test
    [Documentation]  Test case doc
    Log  1
    FOR  ${index}  IN RANGE  0  10
        This Is Keyword
    END
    Keyword
     Keyword2
	 Keyword

Templated Test
    [Documentation]  doc
    [Template]  Some Template
                Over Indent
                ...  Same Here
    What Goes
     [Teardown]  Over Indented

Short Test
    [Setup]  Setup
     Keyword

Mixed Whitespace But Visually Good
     [Documentation]  doc
    Keyword
 	Keyword
    Keyword

*** Keywords ***
This Is Keyword
    [Documentation]  Keyword doc
    [Tags]  tag
    FOR  ${elem}  IN  elem1  elem2  elem3
     ...  elem4
        Log  ${elem}  # this is valid comment
       Keyword

    END
    FOR  ${elem}  IN  elem1  elem2  elem3
    Keyword
    END
   # under-indented comment


### Some header comment ###
## other comment
Other Keyword
  [Documentation]  doc
  Should Be Keyword Call
  Testing
  FOR
  END

Another Keyword
    FOR  ${elem}  IN  ${list}
   Log  stuff
    END

Old For Loop Style
    FOR  ${elem}  IN  ${list}
    /  Keyword
    /   OtherKeyword
    /  Keyword
    /
    /  Previous Is Empty