*** Settings ***
Library     Collections
Library     libs/MyLibrary.py
Library     libs/missing.py
Library     NotInstalledLibrary
Library     ${LIB_DIR}/MyLibrary.py
Library     ${UNDEFINED_DIR}/other.py
Library     Remote    http://127.0.0.1:9999

*** Variables ***
${LIB_DIR}      libs

*** Test Cases ***
Test
    My Keyword
