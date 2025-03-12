*** Variables ***
# standalone      comment
${VALID}          Value
MyVar             val1    val2    val3    val4    val5    val6    val7
...               val8    val9    val10    # var comment
# robocop: fmt: off=NormalizeNewLines
# standalone

*** Test Cases ***  # robocop: fmt: off=NormalizeNewLines


Test
    [Documentation]    This is a documentation
    ...    in two lines
    Some Lines
    No Operation
    [Teardown]    1 minute    args

Test Without Arg
Mid Test
    My Step 1    args    args 2    args 3    args 4    args 5    args 6
    ...    args 7    args 8    args 9    # step 1 comment

*** Keywords ***  # robocop: fmt: off=IDontExist,NormalizeNewLines
Keyword
    No Operation
Other Keyword
Another Keyword
    There
    Are
    More
*** Settings ***
Library  library.py