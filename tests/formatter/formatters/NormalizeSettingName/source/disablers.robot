*** Settings ***
library  # robocop: fmt: off
documentation    This is example documentation
...              which is also multiline  # robocop: fmt: off
# robocop: fmt: off
FORCE TAGS  tag1     tag2
test Template  Keyword


*** Test Cases ***
Test
    [setup]    Keyword2    # robocop: fmt: off
    No Operation
    [ TEARDOWN ]    # robocop: fmt: off


*** Keywords ***  # robocop: fmt: off
Keyword
    [arguments]    ${arg}
    Pass
