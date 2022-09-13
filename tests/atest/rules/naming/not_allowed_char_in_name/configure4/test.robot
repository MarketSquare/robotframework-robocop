*** Test Cases ***
Test with not allowed foo.
    Steps

Test with allowed foo.bar
    Steps

*** Keywords ***

Keyword With not allowed foo.
    No Operation

Keyword With ${em.bedded} and not allowed foo.
    No Operation

Keyword With ${em.bedded} and foo.a ${second} not allowed bar.b
    No Operation

Keyword With allowed foo.bar
    No Operation
