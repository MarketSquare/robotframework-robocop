*** Settings ***
Library    DateTime
Library    Collections
Library    OperatingSystem
Library    XML
Library    String
Library    RequestsLibrary
Resource   ..${/}Libs${/}MyResource.robot
Library    OwnLib.py
Variables    variables.py
Test Template    Keyword


*** Keywords ***
Keyword
    No Operation
