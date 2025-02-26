*** Test Cases ***
Tests with groups
    GROUP
      2 spaces
       3 spaces
    END
    GROUP    Named
      2 spaces
       3 spaces
    END
    GROUP
        GROUP
            Single
        END
       GROUP  Misaligned
             Single
         END
    END
