*** Settings ***
Test Template    Template
Tags    tag
...   tag2
# fmt: off
Suite Setup Keyword
Documentation    Suite documentation

*** Test Cases ***
Test
    No Operation

# robocop: fmt: off


*** Keywords ***
Keyword
    Other Keyword

# robocop: fmt: off

Other Keyword ${embed}
    RETURN    ${embed}
