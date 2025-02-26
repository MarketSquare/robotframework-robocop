*** Settings ***
Library    DateTime
Library    RequestsLibrary
Resource   CustomResource.resource
Resource   AnotherFile.resource
Resource   ..${/}Libs${/}MyResource.robot

Variables    variables.py
Test Template    Keyword


*** Keywords ***
Keyword
    No Operation
