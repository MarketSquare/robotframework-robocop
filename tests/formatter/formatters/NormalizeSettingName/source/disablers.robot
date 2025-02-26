*** Settings ***
library  # robotidy: off
documentation    This is example documentation
...              which is also multiline  # robotidy: off
# robotidy: off
FORCE TAGS  tag1     tag2
test Template  Keyword


*** Test Cases ***
Test
    [setup]    Keyword2    # robotidy: off
    No Operation
    [ TEARDOWN ]    # robotidy: off


*** Keywords ***  # robotidy: off
Keyword
    [arguments]    ${arg}
    Pass
