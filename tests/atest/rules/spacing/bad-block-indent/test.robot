*** Settings ***
Documentation  doc


*** Test Cases ***
Golden test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More

Test with matching indent but not multiple of 4
   [Setup]    Keyword
   Keyword Call

Test with FOR
    Keyword Call
    FOR    ${var}    IN    RANGE    10
   No Operation
    Bad Indent
      FOR    ${var}    IN    a    b
            No Operation
             But Unmatched
             With Others
               ...  Should Be Ignored
             # valid comment
            # invalid - not counted to indent count, but reported if it breaks rule
            # invalid - same as above
      END
      ${assign}    Keyword Call    b
      ...    a
    END

Test with IF
    IF    ${condition}


    ELSE IF    $condition
        IF    $var    No Operation    ELSE    RETURN
        ${assign}    IF    $condition    Set Variable    1    ELSE IF    $other_condition    Keyword
        ...    ${a}
         No Operation
     ELSE
        # comment
        No Operation
# comment
        # comment
    END

Test with WHILE
    WHILE    $condition
         WHILE    $condition
           No Operation
           No Operation
           BREAK
           CONTINUE
         END
        No Operation
        No Operation
        No Operation
    END

Test With TRY
    No Operation
     TRY
        No Operation
         No Operation
        No Operation
    EXCEPT    *
        No Operation
         No Operation
        No Operation
    ELSE
             No Operation
             No Operation
             No Operation
    FINALLY
        No Operation
         No Operation
    No Operation
    END

Templated Test
    [Documentation]  doc
    [Template]  Some Template
                Over Indent
                ...  Same Here
    What Goes
     [Teardown]  Over Indented


*** Keywords ***
Keyword With Uneven NewLines
    [Arguments]    ${arg}
   ...    ${arg2}
    Keyword 1
    Keyword
      ...  ${2}

Keyword With Assignments
    ${arg}    ${arg}    Keyword
    ...  multiline
    IF    ${condition}
        ${value}    Correct Indent
          ${arg}  Incorrect Indent
    ELSE IF  ${flag}
         Incorrect Indent
        Correct Indent
    ELSE
        Correct Indent
    END

Keyword With Under Indented For Loop Body
    FOR  ${elem}  IN  ${list}
   Log  stuff
    END

Keyword With Under Indented For Loop Body And Comment
    Keyword
    FOR    ${var}  IN   1  2
        Keyword
# invalid comment
    END

Golden
    Keyword Call
    FOR  ${var}  IN  1  2
        IF    ${var}
            IF    $condition    RETURN
            Keyword Call    ${var}
             ...    misaligned but different rule
        END
    END

Golden With Comments
    Keyword Call
    # comment
    FOR  ${var}  IN  1  2
        # comment
        IF    ${var}
            # comment
            IF    $condition    RETURN
            Keyword Call    ${var}
             ...    misaligned but different rule
            # comment
        END
    END

# standalone comment

Bad Comment Indent
    Keyword Call
   # comment
    FOR  ${var}  IN  1  2
         # comment
        IF    ${var}
           # comment
            IF    $condition    RETURN
            Keyword Call    ${var}
             ...    misaligned but different rule
             # comment
        END
    END
    # valid

# standalone comment

  # invalid

# valid

Golden With Comments
    Keyword Call
    # comment
    FOR  ${var}  IN  1  2
        # comment
        IF    ${var}
            # comment
            IF    $condition    RETURN
            Keyword Call    ${var}
             ...    misaligned but different rule
            # comment
        END
    END

# standalone comment

Keyword with empty if
   IF  ${False}
   END
