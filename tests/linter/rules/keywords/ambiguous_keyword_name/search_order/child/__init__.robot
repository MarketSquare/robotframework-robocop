*** Settings ***
Library        ../LibOne.py
Library        ../LibTwo.py
Suite Setup    Set Library Search Order    LibTwo
