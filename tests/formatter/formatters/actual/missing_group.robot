*** Settings ***
Documentation  doc  # this is comment
...  another line
Metadata  value  param

Suite Setup  Keyword
# We all
# are commenting Suite Teardown
Suite Teardown  Keyword2
# i want to be keep together with Test Setup
Test Setup  Keyword
Test Timeout  1min

*** Keywords ***