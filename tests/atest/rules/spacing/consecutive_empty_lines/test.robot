*** Settings ***


Test Template    Keyword


Test Timeout    1 min



*** Variables ***


${var}    1


@{var2}    1
...       2
...       3



*** Test Cases ***


Test case 1

    Keyword


    Keyword


Test case 2
    Keyword
    Keyword



*** Keywords ***


Keyword 1

    Keyword



    Keyword


Keyword 2
    Keyword
    Keyword

