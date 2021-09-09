*** Settings ***
Library  Collections
Resource  data.resource
Variables  vars.robot

Force Tags  tag
...  tag2

Default Tags tag

Suite Setup  Keyword
Suite Teardown  Keyword
Test Setup  Keyword
Test Teardown  Keyword
Test Timeout  1 day
Test Template  Keyword

Documentation  doc
Metadata  meta  data
