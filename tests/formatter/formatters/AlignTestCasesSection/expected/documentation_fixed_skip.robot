*** Settings ***
Documentation    Do not touch this.


*** Test Cases ***
Example of alignment to second column of Documentation
    [Documentation]     Unselects checkbox value in the data table
    ...                 note that you must give some unique column/value pair that is used to select the row
    ...
    ...                 == Examples ==
    ...                 # makes sure checkbox is unchecked in column Owner in a row where Name is "NORDEA FINANS"
    ...                 Table_CheckboxUnSelect  Owner      Name    NORDEA FINANS

Test with documentation and keyword calls
  [Documentation]    Do stuff.
    Longer Keyword Call That Ends Here

Test with documentation and keyword calls 2
    [Documentation]    Do stuff.
    ...   2nd
    Longer Keywordsss       ${arg}

Test With Empty Documentation
    [Documentation]

Test with documentation and other settings
    [Documentation]    Do stuff
    ...                   Also multiline    Extra whitespace
    ...                       Only fix indent.
    [Tags]                  ${arg}                  ${arg2}
