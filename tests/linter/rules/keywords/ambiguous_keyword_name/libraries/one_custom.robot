*** Settings ***
Library    Collections
Library    CopyOne.py


*** Test Cases ***
Custom Library Wins Over Standard Library
    ${copy}    Copy List    ${{[]}}
