*** Settings ***
Library    Collections
Library    CopyOne.py
Library    CopyTwo.py


*** Test Cases ***
Two Custom Libraries And Standard Library
    ${copy}    Copy List    ${{[]}}
