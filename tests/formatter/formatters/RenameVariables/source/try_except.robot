*** Keywords ***
Keyword With Try
     ${local} =    Keyword
     TRY
         Do Stuff    ${local}    ${global}
     EXCEPT    Error    AS    ${ERROR}
         Log    ${ERROR}
     END
