*** Test Cases ***
FOR loop
    FOR  ${var}  IN  1  2  3
       ${variable}    Keyword    ${var}
       Another Keyword
       Keyword That Goes Over Limit Of The Column    ${short}    ${loooooooooooooooooooooooooooong}
    END

Nested FOR loop
    FOR  ${var}  IN  1  2  3
       ${variable}    Keyword    ${var}
       Another Keyword
       FOR  ${var2}  IN  1  2  3
           Short   1   2
           ${assign}    Longer Keyword
           ...    ${multiline}    ${arg}
       END
       Keyword That Goes Over Limit Of The Column    ${short}    ${loooooooooooooooooooooooooooong}
    END

IF
    IF    ${condition}
       ${variable}    Keyword    ${var}
       Another Keyword
    ELSE IF    $flag
       ${variable}    Keyword    ${var}
       Another Keyword
    ELSE
       ${variable}    Keyword    ${var}
       Another Keyword
    END
