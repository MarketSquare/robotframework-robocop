*** Test Cases ***
Simple math operations
    ${i}    Set Variable    ${0}
    Log    ${i+1}

Global Value
    Log    ${i-1}

Invalid syntax
    ${i}    Set Variable    ${0}
    ${y}    Set Variable    ${1}
    Log    ${i+y+1}

All examples
    ${string} =    Set Variable    abc
    ${bignum} =    Set Variable    ${1234}
    ${number} =    Set Variable    ${2}

    Log    Addition
    Log    ${number + 1}
    Log    ${number + -2}
    Log    ${number + - 2}
    Log    ${number +- 2}
    Log    ${number + ${number} + 1}
    Log    ${number + ${number + 1}}

    Log    Other Arithmetic
    Log    ${number - 1}
    Log    ${number * 1}
    Log    ${number / 1}
    Log    ${bignum % ${number}}
    Log    ${number ** 4}
    Log    ${number // ${number}}

    Log    Inline Comparison
    Log    ${number == 1}
    Log    ${number == ${1}}
    Log    ${number == ${number}}
    Log    ${number != ${number}}
    Log    ${number > ${number}}
    Log    ${number < ${number}}
    Log    ${number >= ${number}}
    Log    ${number <= ${number}}

    Log    Bitwise Operations
    Log    ${number & 1}
    Log    ${number | 1}
    Log    ${number | ~ 1}
    Log    ${number ^ 1}
    Log    ${number << 1}
    Log    ${number >> 1}

One-sided spaces
    ${number} =    Set Variable    ${1}
    Log    ${number +1}
    Log    ${number+ 1}
    Log    ${number + -2}
    Log    ${number +-2}
    Log    ${number+- 2}
    Log    ${number +-2}

Variable with spaces
    ${var with spaces} =    Set Variable    ${1}
