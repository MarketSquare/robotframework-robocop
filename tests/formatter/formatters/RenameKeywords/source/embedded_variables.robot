*** Keywords ***
Embedded ${variables} That should Be ${ignored.and.dots}
    Login With '{user.uid}'_and '${user.password}' to Check_Validation

Variable With Square Brackets
    normalize_this${variable['test']}
    normalize_this${variable}['test']

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
