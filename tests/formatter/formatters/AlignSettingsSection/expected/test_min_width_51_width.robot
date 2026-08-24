*** Settings ***
# whole line comment that should be ignored
Resource                                           ..${/}resources${/}resource.robot
Library                                            SeleniumLibrary
Library                                            Mylibrary.py
Variables                                          variables.py
Test Timeout                                       1 min

# this should be left aligned
Library                                            CustomLibrary    WITH NAME    name
Library                                            ArgsedLibrary    ${1}    ${2}    ${3}

Documentation                                      Here is some regular text that should be formatted
...
...                                                | This pre-formatted text should stay intact
...                                                |    1.2 <----> 1.2    .--> 1.2
...                                                |    1.3 <-.    1.3 <-´ ,-> 1.3
...                                                |    1.4    `-> 1.4    /    1.4
...                                                |    1.5        1.5 <-´     1.5

Default Tags                                       default tag 1    default tag 2    default tag 3    default tag 4    default tag 5
Test Setup                                         Open Application    App A
Test Teardown                                      Close Application

Metadata                                           Version    2.0
Metadata                                           More Info    For more information about *Robot Framework* see http://robotframework.org
Metadata                                           Executed At    {HOST}
# this should be left aligned
Test Template

*** Keywords ***
Keyword
    Keyword  A
    Keyword    B
