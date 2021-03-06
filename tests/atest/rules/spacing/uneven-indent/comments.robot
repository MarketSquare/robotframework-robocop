*** Settings ***
Documentation    doc
# this is valid comment
  # this is invalid comment
Force Tags    tag


*** Variables ***
# comment
${VAR}  1

# another comment
${VAR1}  2
  # invalid comment


*** Test Cases ***
# valid comment
  # invalid comment
Test1
    Keyword
    # comment
  # invalid comment

# comment
    # now also invalid

Test2
    Keyword
    FOR    ${var}  IN   1  2
        Keyword
# invalid comment
    END

*** Keywords ***
Keyword1
    Keyword
    # comment
  # invalid comment

# comment

Keyword2
    Keyword
    FOR    ${var}  IN   1  2
        Keyword
# invalid comment
    END
