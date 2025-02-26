
# this is comment section
*** Keywords ***
Keyword
    No Operation

*** Test Cases ***
Test 1
    Log  1

Test 2
    Log  2

*** Settings ***
Library  somelib.py
Test Template    Template


*** Keyword ***
Keyword2
    Log  2
    FOR  ${i}  IN RANGE  10
        Log  ${i}
    END

*** Test Cases ***
Test 3
    Log  3


*** Variables ***  this should be left  alone
${var}  1
@{var2}  1
...  2


*** settings***
Task Timeout  4min

Force Tags  sometag  othertag
