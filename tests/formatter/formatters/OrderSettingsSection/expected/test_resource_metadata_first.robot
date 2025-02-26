*** Settings ***
Metadata  value  param
Documentation  doc  # this is comment
...  another line

Resource    robot.resource
Library  Collections
Library  Stuff
Library  stuff.py  WITH NAME  alias
Variables   variables.py

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