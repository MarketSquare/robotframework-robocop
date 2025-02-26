*** Test Cases ***
Simple IF
    IF  $condition1  Keyword  argument
    IF  $condition1  RETURN
    IF  $condition1  CONTINUE
    IF  $condition  BREAK

Nested IF
    FOR  ${var}  IN RANGE  10
        IF  $condition1  Keyword  argument  # comment
    END

ELSE IF
    IF  ${condition}  Keyword Call  ELSE  Keyword Call 2
    ${assign}  IF  ${{ inline eval }}  Keyword Call  ${arg}  ELSE IF  $flag  Keyword Call 2
