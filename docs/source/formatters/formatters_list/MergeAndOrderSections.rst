.. _MergeAndOrderSections:

MergeAndOrderSections
==================================

Merge duplicated sections and order them.

.. |FORMATTERNAME| replace:: MergeAndOrderSections
.. include:: enabled_hint.txt

Default order is: Comments > Settings > Variables > Test Cases > Keywords.

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            # this is comment section
            *** Keywords ***
            Keyword
                No Operation

            *** Test Cases ***
            Test 1
                Log  1

            Test 2
                Log  2

            *** Settings ***
            Library  somelib.py
            Test Template    Template


            *** Keyword ***
            Keyword2
                Log  2
                FOR  ${i}  IN RANGE  10
                    Log  ${i}
                END

            *** Test Cases ***
            Test 3
                Log  3


            *** Variables ***  this should be left  alone
            ${var}  1
            @{var2}  1
            ...  2


            *** settings***
            Task Timeout  4min

            Force Tags  sometag  othertag

    .. tab-item:: After

        .. code:: robotframework

            *** Comments ***

            # this is comment section
            *** Settings ***
            Library  somelib.py
            Test Template    Template


            Task Timeout  4min

            Force Tags  sometag  othertag
            *** Variables ***  this should be left  alone
            ${var}  1
            @{var2}  1
            ...  2


            *** Test Cases ***
            Test 1
                Log  1

            Test 2
                Log  2

            Test 3
                Log  3


            *** Keywords ***
            Keyword
                No Operation

            Keyword2
                Log  2
                FOR  ${i}  IN RANGE  10
                    Log  ${i}
                END

Custom order
-------------

You can change sorting order by configuring ``order`` parameter with comma separated list of section names (without
spaces)::

    robocop format --configure MergeAndOrderSections.order=settings,keywords,variables,testcases,comments

Miscellaneous
--------------

Because merging and changing the order of sections can shuffle your empty lines it's greatly advised to always
run ``NormalizeNewLines`` transformer after this one. This is done by default so this advice apply only if you're
running transformers separately.

If both ``*** Test Cases ***`` and ``*** Tasks ***`` are defined in one file they will be merged into one (header
name will be taken from first encountered section).

Any data before first section is treated as comment in Robot Framework. This transformer add ``*** Comments ***``
section for such lines:

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            i am comment
            # robocop: off
            *** Settings ***

    .. tab-item:: After

        .. code:: robotframework

            *** Comments ***
            i am comment
            # robocop: off
            *** Settings ***

You can disable this behaviour by setting ``create_comment_section`` to False::

    robocop format --configure MergeAndOrderSections.create_comment_section=False

