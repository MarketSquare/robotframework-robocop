*** Settings ***
Metadata  value  param



Documentation  doc  # this is comment
...  another line
Test Timeout  1min

# i want to be keep together with Test Setup

Test Setup  Keyword


Suite Setup  Keyword

# We all
# are commenting Suite Teardown
Suite Teardown  Keyword2




*** Keywords ***