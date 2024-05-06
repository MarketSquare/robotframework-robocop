Variables in FOR loop option not recognized by unused-argument (#1073)
----------------------------------------------------------------------

Variables in FOR option should be now recognized by W0919 ``unused-argument``::

    *** Keywords ***
    Keyword With For
        [Arguments]    ${argument}
        # ${argument} will no longer issue unused-argument
        FOR    ${index}    ${value}    IN ENUMERATE    @{LIST}    start=${argument}
            Log    ${value}
        END
