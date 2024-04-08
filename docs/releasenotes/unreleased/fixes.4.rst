Tags in documentation
----------------------

Keyword tags can be specified on the last line of the documentation with ``Tags:`` prefix. It was handled by Robocop
already but not all tags were parsed correctly. For example::

    *** Keywords ***
    Already working
    [Documentation]    Tags: tag
        Step

    Multiple tags not supported before
    [Documentation]    Tags: tag1, tag2
        Step

    Multiple spaces not supported before
    [Documentation]    Tags:  tag1,    tag2
        Step
