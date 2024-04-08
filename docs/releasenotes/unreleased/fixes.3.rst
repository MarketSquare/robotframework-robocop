Ignore variables in tags (#1059)
--------------------------------

Variables in tags are now not checked by tag rules but variable rules only.

For example::

    *** Test Cases ***
    Test with dynamic tag
        [Tags]    tag${GLOBAL VARIABLE}
        Step

Will now not raise W0601 ``tag-with-space`` since the space is inside variable name.
