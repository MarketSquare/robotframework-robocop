*** Settings ***
Force Tags  tag
...  tag
Default Tags  1

Documentation  doc  # this is comment
...  another line
Metadata  value  param

Library  Collections
Library  Stuff
Library  stuff.py  WITH NAME  alias
Resource    robot.resource
Variables   variables.py

Suite Setup  Keyword
# We all
# are commenting Suite Teardown
Suite Teardown  Keyword2
# i want to be keep together with Test Setup
Test Setup  Keyword
Test Timeout  1min

*** Keywords ***