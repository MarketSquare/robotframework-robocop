*** Keywords ***
Embedded ${variables} That Should Be ${ignored.and.dots}
    Login With '{user.Uid}' And '${user.password}' To Check Validation

Variable With Square Brackets
    Normalize This${variable['test']}
    Normalize This${variable}['test']

Invalid Syntax
    Not Closed ${var

Multiple In A Row
    Verstuur RTR ${project} ${operatie} ${opdracht}

Empty Space After Last Variable
    Embedded ${variable} And Space

Embedded Last
    Embedded ${variable}
    Embedded ${variable}    ${argument}

Run Keyword
    Run Keywords     ${keyword}
