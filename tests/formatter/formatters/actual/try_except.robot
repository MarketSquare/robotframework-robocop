*** Keywords ***
Keyword With Try
     ${local} =    Keyword
     TRY
         Do Stuff    ${local}    ${GLOBAL}
     EXCEPT    Error    AS    ${error}
         Log    ${error}
     END
