Comments section with only robocop disabler raising ignored-data (#1044)
------------------------------------------------------------------------

Following code will not raise W0704 ``ignored-data`` anymore since comments section contains only robocop disabler and
empty lines::

    # robocop: off=0701

    *** Test Cases ***
    First Test Case
        [Documentation]    Doc
        No Operation
