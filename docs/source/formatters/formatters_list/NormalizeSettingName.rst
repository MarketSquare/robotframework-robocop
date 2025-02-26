.. _NormalizeSettingName:

NormalizeSettingName
================================

Normalize setting name.

.. |FORMATTERNAME| replace:: NormalizeSettingName
.. include:: enabled_hint.txt

Ensure that setting names are title case without leading or trailing whitespace.

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***
            library    library.py
            test template    Template
            FORCE taGS    tag1

            *** Keywords ***
            Keyword
                [arguments]    ${arg}
                [TEARDOWN]   Teardown Keyword

    .. tab-item:: After

        .. code:: robotframework

            *** Settings ***
            Library    library.py
            Test Template    Template
            Force Tags    tag1

            *** Keywords ***
            Keyword
                [Arguments]    ${arg}
                [Teardown]   Teardown Keyword
