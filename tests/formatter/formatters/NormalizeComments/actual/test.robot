##comment
# comment
# comment
#  comment
#    comment
# robocop: fmt: off
# robocop: fmt: on


*** Settings ***
# comment
# comment
#  comment
#    comment
# robocop: fmt: off
# robocop: fmt:  on
Suite Setup    Keyword  # comment
Suite Teardown  Keyword  # comment
Default Tags    tag
...  tag2  # comment


*** Variables ***
# comment
# comment
#  comment
#    comment
# robocop: fmt: off
# robocop: fmt:  on

${VARIABLE}  # comment
@{LIST
...  element  # comment

*** Test Cases ***
# comment
# comment
#  comment
#    comment
# robocop: fmt: off
# robocop: fmt:  on

Test Case
    # comment
    Step
    ...  arg  # comment
    ${assign}  # comment
    ...    ${assign2}  # Comment
    Keyword

*** Keywords ***
# comment
# comment
#  comment
#    comment
# robocop: fmt: off
# robocop: fmt:  on

Keyword
    # comment
    Step
    ...  arg  # comment
    FOR    ${var}    IN   ${LIST}  # comment
        # comment
        Step
        ...  arg  # comment
    END
    TRY  # comment
        # comment
    FINALLY
        # comment
    END
