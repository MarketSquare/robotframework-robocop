*** Settings ***
Documentation  doc  # this is comment
...  another line
Metadata  value  param

Variables   variables.py
Library  Stuff
Library  Collections
Resource    robot.resource
Library  stuff.py  WITH NAME  alias

Suite Setup  Keyword
# We all
# are commenting Suite Teardown
Suite Teardown  Keyword2
# i want to be keep together with Test Setup
Test Setup  Keyword
Test Timeout  1min

Force Tags  tag
...  tag
Default Tags  1

*** Keywords ***