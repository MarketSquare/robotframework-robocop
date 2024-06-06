*** Settings ***
Library    DateTime
Library    Collections
Library    OperatingSystem
Library    XML
Library    String
Library    OwnLib.py
Library    RequestsLibrary
Library    AnotherLibrary
Resource   ..${/}Libs${/}MyResource.robot

Variables    variables.py
Test Template    Keyword


*** Keywords ***
Keyword
    No Operation
