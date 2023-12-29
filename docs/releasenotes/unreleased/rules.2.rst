Recognize keywords in Pabot run keywords (#1014)
------------------------------------------------

Keywords used in Pabot run keywords such as ``Run Setup Only Once`` are now recognized as keywords by Robocop rules::

    *** Keywords ***
    Keyword Run In Parallel
        Run Only Once    keyword  # should raise wrong-case-in-keyword-name
