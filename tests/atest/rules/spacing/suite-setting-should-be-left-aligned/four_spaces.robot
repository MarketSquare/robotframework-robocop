*** Settings ***
    Library  Collections
    Resource  data.resource
    Variables  vars.robot

    Force Tags  tag
    ...  tag2

    Default Tags  tag

    Suite Setup  Keyword
    Suite Teardown  Keyword
    Test Setup  Keyword
    Test Teardown  Keyword
    Test Timeout  1 day
    Test Template  Keyword

    Documentation  doc
    Metadata  meta  data


*** Variables ***
 ${MY VAR}  10
  ${MY VAR1}  10
   ${MY VAR2}  10
    ${MY VAR3}  10
${GOLD VAR}  10
  ${NOT_ALIGNED}  1
...  2
${ALIGNED}  1
...  2


*** Test Cases ***
Test
    [Documentation]  doc
    Log  ${MY VAR}
