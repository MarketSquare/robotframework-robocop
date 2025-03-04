*** Settings ***
Library Collections
Resource file.robot
Variablesvars.yaml

Force Tags tag
...    tag2
Default Tagstag1    tag2

Invalid  ${argument}

Timeout 1min
Suite Setup Keyword
Suite Teardown Keyword2

Test Setup Keyword
Test Teardown Keyword2
Testtimeout 1min
Documentation this is doc

Metadata key value

*** Keywords ***
Keyword With Invalid Setting
    [Doc Umentation]
