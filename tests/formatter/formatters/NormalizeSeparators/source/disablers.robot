

*** Settings ***
Library  library.py  WITH NAME          alias  # robocop: fmt: off

Force Tags           tag
...   tag  # robocop: fmt: off
# robocop: fmt: off
Documentation  doc
...      multi
...  line

*** Variables ***
${var}     3  # robocop: fmt: off
# robocop: fmt: off
 ${var2}  4

*** Test Cases ***
Test case
  # robocop: fmt: off
  [Setup]  Keyword
   Keyword  with  arg
   ...  and  multi  lines
     [Teardown]          Keyword
# robocop: fmt: off
Test case with structures
    FOR  ${variable}  IN  1  2
    Keyword
     IF  ${condition}
       Log  ${stuff}  console=True
  END
   END

*** Keywords ***  # robocop: fmt: off
Keyword
Another Keyword
          [Arguments]  ${arg}  # robocop: fmt: off
       Should Be Equal  1  # robocop: fmt: off
       ...  ${arg}
   # robocop: fmt: off
   IF  ${condition}
        FOR  ${v}  IN RANGE  10
   Keyword
        END
   END

Keyword With Tabulators
    Keyword
    ...  2
	...  ${arg}
