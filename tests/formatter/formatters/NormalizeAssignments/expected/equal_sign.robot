*** Variables ***
${var}  ${1}
@{list}  a
...  b
...  c

${variable}  10


*** Keywords ***
Keyword
    ${var}=  Keyword1
    ${var}=   Keyword2
    ${var}=    Keyword

Attribute Access
    ${DAT}[ReturnValue]=    Generate Random String    length=${DAT}[InputValue]
