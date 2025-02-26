

*** Settings ***
Library  library.py  WITH NAME          alias  # robotidy: off

Force Tags           tag
...   tag  # robotidy: off
# robotidy: off
Documentation  doc
...      multi
...  line

*** Variables ***
${var}     3  # robotidy: off
# robotidy: off
 ${var2}  4

*** Test Cases ***
Test case
  # robotidy: off
  [Setup]  Keyword
   Keyword  with  arg
   ...  and  multi  lines
     [Teardown]          Keyword
# robotidy: off
Test case with structures
    FOR  ${variable}  IN  1  2
    Keyword
     IF  ${condition}
       Log  ${stuff}  console=True
  END
   END

*** Keywords ***  # robotidy: off
Keyword
Another Keyword
          [Arguments]  ${arg}  # robotidy: off
       Should Be Equal  1  # robotidy: off
       ...  ${arg}
   # robotidy: off
   IF  ${condition}
        FOR  ${v}  IN RANGE  10
   Keyword
        END
   END

Keyword With Tabulators
    Keyword
    ...  2
	...  ${arg}
