*** Comments ***

# this is comment section
*** Settings ***
Library  somelib.py
Test Template    Template


Task Timeout  4min

Force Tags  sometag  othertag
*** Variables ***  this should be left  alone
${var}  1
@{var2}  1
...  2


*** Test Cases ***
Test 1
    Log  1

Test 2
    Log  2

Test 3
    Log  3

# robocop: fmt: off
*** Keywords ***
Keyword
    No Operation

Keyword2
    # robocop: fmt: off
    Log  2
    FOR  ${i}  IN RANGE  10
        Log  ${i}
    END

