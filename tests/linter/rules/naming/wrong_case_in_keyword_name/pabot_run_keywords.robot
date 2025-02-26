*** Settings ***
Suite Setup    Run Setup Only Once    some keyword
Suite Teardown    PabotLib.Run Teardown Only Once    some keyword

*** Keywords ***
Keyword Run In Parallel
    Run Only Once    keyword
    Pabotlib.Run On Last Process    keyword
