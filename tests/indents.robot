*** Settings ***
Documentation  This is suite doc

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

*** Keywords ***
This Is Keyword
    [Documentation]  Keyword doc
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
  Should Be KeywordCall
  Testing
  FOR
  END

Another Keyword
    FOR  ${elem}  IN  ${list}
   Log  stuff
    END
