*** Settings ***
library
documentation    This is example documentation
...              which is also multiline
FORCE TAGS  tag1     tag2
test Template  Keyword


*** Test Cases ***
Test
    [setup]    Keyword2
    No Operation
    [Teardown]


*** Keywords ***
Keyword
    [arguments]    ${arg}
    Pass
