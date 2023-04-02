*** Variables ***
${MY_VAR}  1
${MY VAR}  2
${MYVAR}   3
${my_var}  4
${My Var}  5
${my var}  6
${MyVar}   7
${My_Var}  8
${myVar}   9
${MY_var}  10

${MY_VAR${var}}  11
${MY VAR${VAR}}  11
${${var}MY VAR${VAR}}  11
${${var${VAR}}MY VAR${VAR}}  11
${@{VAR}[1]MY_VAR&{var.param}}  11
${${var${VAR}}my_var}  11
${${VAR}my_var}  11
${${VAR}my_var${var}}  11
${@{VAR}[1]my_var}  11
${@{VAR}[1]my_var&{var.param}}  11


*** Test Cases ***
Test
    Pass
