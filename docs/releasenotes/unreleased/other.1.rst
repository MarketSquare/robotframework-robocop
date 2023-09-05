Disabler keyword are now consistent with Robotidy (#933)
--------------------------------------------------------

Disabling the line from the linting can be done using disabler comment::

    # robocop:disable=rule_name

Robotidy also supports disablers but using different keywords::

    # robotidy:off

We have decided to make it more consistent and use ``on`` and ``off`` markers (mimicking [Robotidy tool](https://github.com/MarketSquare/robotframework-tidy)) instead of ``enable`` and
``disable``. Both types of the markers are supported but ``on`` and ``off`` are now recommended.
