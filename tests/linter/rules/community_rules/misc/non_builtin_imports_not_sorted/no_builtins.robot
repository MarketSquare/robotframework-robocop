*** Settings ***
Library    RequestsLibrary
Resource   ..${/}Libs${/}MyResource.robot
Library    OwnLib.py
Variables    variables.py
Test Template    Keyword


*** Keywords ***
Keyword
    No Operation
