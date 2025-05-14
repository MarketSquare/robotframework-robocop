*** Settings ***
# whole line comment that should be ignored
Resource            ..${/}resources${/}resource.robot
Library             SeleniumLibrary
Library             Mylibrary.py
Variables           variables.py
Test Timeout        1 min

# robocop: fmt: off
    # this should be left aligned
Library    CustomLibrary   WITH NAME  name
Library    ArgsedLibrary   ${1}  ${2}  ${3}
# robocop: fmt: on

Documentation       Example using the space separated format.
...                 and this documentation is multiline
...                 where this line should go I wonder?

Default Tags       default tag 1    default tag 2    default tag 3    default tag 4    default tag 5  # robocop: fmt: off
Test Setup          Open Application    App A
Test Teardown       Close Application

Metadata            Version    2.0
Metadata            More Info    For more information about *Robot Framework* see http://robotframework.org
Metadata            Executed At    {HOST}
# this should be left aligned
Test Template

*** Keywords ***
Keyword
    Keyword  A
    Keyword    B
