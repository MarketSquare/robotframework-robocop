Robocop file disablers can be defined anywhere in the first comment section (#1044)
-----------------------------------------------------------------------------------

It was possible to disable Robocop for selected or all rules in the given file. However such disablers had to be defined
in the the first line of the file::

    # robocop: off

    *** Test Cases ***
    Test
        Step

It is now also possible to define file-level disablers anywhere in the first comment section::

    # robocop: off=onerule
    # explanation why the rule is disabled
    # robocop: off=onerule2

    *** Test Cases ***
    Test
        Step
