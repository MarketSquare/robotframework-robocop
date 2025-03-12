.. _DiscardEmptySections:

DiscardEmptySections
================================

Remove empty sections.

.. |FORMATTERNAME| replace:: DiscardEmptySections
.. include:: enabled_hint.txt

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***


            *** Test Cases ***
            Test
                [Documentation]  doc
                [Tags]  sometag
                Pass
                Keyword
                One More


            *** Keywords ***
            # This section is not considered empty.


            *** Variables ***

            *** Comments ***
            robocop: disable=all

    .. tab-item:: After

        .. code:: robotframework

            *** Test Cases ***
            Test
                [Documentation]  doc
                [Tags]  sometag
                Pass
                Keyword
                One More


            *** Keywords ***
            # This section is not considered empty.


            *** Comments ***
            robocop: disable=all


Remove sections only with comments
-----------------------------------

Sections are considered empty if there are only empty lines inside.
You can remove sections with only comments by setting ``allow_only_comments`` parameter to False. ``*** Comments ***``
section with only comments is always considered as non-empty::

    robocop format --configure DiscardEmptySection.allow_only_comments=True

.. tab-set::

    .. tab-item:: alloow_only_comments=True (default)

        .. code:: robotframework

            *** Test Cases ***
            Test
                [Documentation]  doc
                [Tags]  sometag
                Pass
                Keyword
                One More

            *** Keywords ***
            # This section is considered to be empty.

            *** Comments ***
            # robocop: off=all

    .. tab-item:: alloow_only_comments=False

        .. code:: robotframework

            *** Test Cases ***
            Test
                [Documentation]  doc
                [Tags]  sometag
                Pass
                Keyword
                One More

            *** Comments ***
            # robocop: off=all

Skip formatting
----------------

It is possible to use the following arguments to skip formatting of the code:

- :ref:`skip sections`

It is also possible to use disablers (:ref:`disablers`) but ``skip`` option
makes it easier to skip all instances of given type of the code.
