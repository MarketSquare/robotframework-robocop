*** Settings ***
Documentation  Tests about number of lines between specific elements
*** Variables ***
${RANDOM_VARIABLE}      True

*** Test Cases ***
First Test Case With 1 Space
    Pass Execution      Wow!

Second Test Case With 2 Spaces
    Pass Execution      Wow!


Third Test Case Without Space
    Pass Execution      Wow!
Last Test Case With 2 Spaces
    Pass Execution      Wow!



*** Keywords *** 
Some Keyword
    Log             I'm just a keyword
