This data is ignored at runtime but should be preserved by Tidy.


*** Variables ***
# standalone      comment
${VALID}          Value
MyVar             val1    val2    val3    val4    val5    val6    val7
...               val8    val9    val10    # var comment
# standalone


*** Test Cases ***
Test    arg1   arg2

Test Without Arg

Mid Test
    My Step 1    args    args 2    args 3


*** Keywords ***
Keyword
    No Operation

Other Keyword

Another Keyword
    There
    Are
    More


*** Settings ***
Library  library.py
Test Template  Template For Tests In This Suite
