*** Settings ***
Library     Collections
Library     DateTime
Library     Dialogs
Library     OperatingSystem
Library     String
Library     XML
Library     Browser
Library     RequestsLibrary
Library     Keywords/MyUtilities.py
Library     Remote    http://localhost:9050/    WITH NAME    JDBCDB2    # DB2
Resource    keywords.robot
Resource    other_stuff.robot
