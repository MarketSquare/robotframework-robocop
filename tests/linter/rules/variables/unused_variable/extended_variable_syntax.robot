*** Keywords ***
Extended Variable Syntax
    ${var1}    ${var2}    ${var3}    ${var4}    ${var5}    ${var6}    ${var7}    ${vaR8}    ${var9}    Keyword Call
    Log    ${var1 + "test"}    level=warn
    Log    ${var2 * 3}    level=warn
    Log    ${var3[1]}    level=warn
    Log    ${var4 == "test"}
    Log    ${var5 == var6}
    Log    ${VAR7[1]}
    Log    ${var5 == var8}
    Log    ${var9.attribute}
