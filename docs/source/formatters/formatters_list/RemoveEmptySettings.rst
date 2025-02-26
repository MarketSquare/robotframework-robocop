.. _RemoveEmptySettings:

RemoveEmptySettings
================================

Remove empty settings.

.. |FORMATTERNAME| replace:: RemoveEmptySettings
.. include:: enabled_hint.txt

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***
            Documentation
            Suite Setup
            Metadata
            Metadata    doc=1
            Test Setup
            Test Teardown    Teardown Keyword
            Test Template
            Test Timeout
            Force Tags
            Default Tags
            Library
            Resource
            Variables

            *** Test Cases ***
            Test
                [Setup]
                [Template]    #  comment    and    comment
                [Tags]    tag
                Keyword

    .. tab-item:: After

        .. code:: robotframework

            *** Settings ***
            Metadata    doc=1
            Test Teardown    Teardown Keyword

            *** Test Cases ***
            Test
                [Tags]    tag
                Keyword

You can configure which settings are affected by parameter ``work_mode``. Possible values:

- overwrite_ok (default) - does not remove settings that are overwriting suite settings (Test Setup,
  Test Teardown, Test Template, Test Timeout or Default Tags)
- always - works on every settings

Empty settings that are overwriting suite settings will be converted to be more explicit (given that there is
related suite settings present). You can disable that behavior by changing ``more_explicit``
parameter value to ``False``::

    robocop format --configure RemoveEmptySettings.more_explicit=False

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***
            Test Timeout  1min
            Force Tags

            *** Test Case ***
            Test
                [Documentation]    Empty timeout means no timeout even when Test Timeout has been used.
                [Timeout]
                No timeout

    .. tab-item:: more_explicit=True (default)

        .. code:: robotframework

            *** Settings ***
            Test Timeout  1min

            *** Test Case ***
            Test
                [Documentation]    Empty timeout means no timeout even when Test Timeout has been used.
                [Timeout]    NONE
                No timeout

    .. tab-item:: more_explicit=False

        .. code:: robotframework

            *** Settings ***
            Test Timeout  1min

            *** Test Case ***
            Test
                [Documentation]    Empty timeout means no timeout even when Test Timeout has been used.
                [Timeout]
                No timeout

If you want to remove all empty settings even if they are overwriting suite settings (like in above example) then
set ``work_mode`` to ``always``::

    robocop format --configure RemoveEmptySettings.work_mode=always

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***
            Test Timeout  1min
            Force Tags

            *** Test Case ***
            Test
                [Documentation]    Empty timeout means no timeout even when Test Timeout has been used.
                [Timeout]
                No timeout

    .. tab-item:: After

        .. code:: robotframework

            *** Settings ***
            Test Timeout  1min

            *** Test Case ***
            Test
                [Documentation]    Empty timeout means no timeout even when Test Timeout has been used.
                No timeout
