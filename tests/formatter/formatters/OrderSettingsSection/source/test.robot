*** Settings ***
Metadata  value  param

Force Tags  tag
...  tag

Documentation  doc  # this is comment
...  another line
Test Timeout  1min

# i want to be keep together with Test Setup

Test Setup  Keyword


Suite Setup  Keyword
Default Tags  1
# We all
# are commenting Suite Teardown
Suite Teardown  Keyword2

Variables   variables.py
Library  Stuff
Library  Collections
Resource    robot.resource
Library  stuff.py  WITH NAME  alias


*** Keywords ***