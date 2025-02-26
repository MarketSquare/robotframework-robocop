.. _SplitTooLongLine:

SplitTooLongLine
================================

Split too long lines.

.. |FORMATTERNAME| replace:: SplitTooLongLine
.. include:: enabled_hint.txt

If line exceeds given length limit (120 by default) it will be split:

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Variables ***
            @{LIST}    value    value2    value3  # let's assume that value2 is at 120 char

            *** Keywords ***
            Keyword
                Keyword With Longer Name    ${arg1}    ${arg2}    ${arg3}  # let's assume that arg2 is at 120 char

    .. tab-item:: After

        .. code:: robotframework

            *** Variables ***
            # let's assume that value2 is at 120 char
            @{LIST}
            ...    value
            ...    value2
            ...    value3

            *** Keywords ***
            Keyword
                # let's assume that arg2 is at 120 char
                Keyword With Longer Name
                ...    ${arg1}
                ...    ${arg2}
                ...    ${arg3}

Missing functionality
----------------------

``SplitTooLongLine`` does not support splitting all Robot Framework types. Currently it will only work on too
long keyword calls, variables and selected settings (tags and arguments). Missing types will be covered in the future
updates.

Allowed line length
--------------------

Allowed line length is configurable using global parameter ``--line-length``::

    robocop format --line-length 140.robot

Or using dedicated for this transformer parameter ``line_length``::

    robocop format --configure SplitTooLongLine.line_length=140.robot

Split argument on every line
----------------------------

Using ``split_on_every_arg`` flag (``True`` by default), you can force the formatter to fill keyword arguments
in one line until character limit::

    robocop format --configure SplitTooLongLine.split_on_every_arg=False

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Keyword
                Keyword With Longer Name    ${arg1}    ${arg2}    ${arg3}  # let's assume that arg2 is at 120 char

    .. tab-item:: After

        .. code:: robotframework

            *** Keywords ***
            Keyword
                # let's assume that arg2 is at 120 char
                Keyword With Longer Name    ${arg1}
                ...    ${arg2}    ${arg3}

Split values on every line
--------------------------

Using ``split_on_every_value`` flag (``True`` by default), you can force the formatter to fill values in one line
until character limit::

    robocop format --configure SplitTooLongLine.split_on_every_value=False

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Variables ***
            # let's assume character limit is at age=12
            &{USER_PROFILE}    name=John Doe    age=12     hobby=coding

    .. tab-item:: After

        .. code:: robotframework

            *** Variables ***
            # let's assume character limit is at age=12
            &{USER_PROFILE}    name=John Doe    age=12
            ...    hobby=coding

Split settings arguments on every line
---------------------------------------

Using ``split_on_every_setting_arg`` flag (``True`` by default), you can force the formatter to fill settings arguments
in one line until character limit::

    robocop format --configure SplitTooLongLine.split_on_every_setting_arg=False

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Arguments
                [Arguments]    ${short}    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
                Step

    .. tab-item:: After (default)

        .. code:: robotframework

            *** Keywords ***
            Arguments
                [Arguments]
                ...    ${short}
                ...    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
                ...    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
                Step

    .. tab-item:: After (split_on_every_setting_arg set to False)

        .. code:: robotframework

            *** Keywords ***
            Arguments
                [Arguments]    ${short}    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
                ...    ${veryLongAndJavaLikeArgumentThatWillGoOverAllowedLength}
                Step

Assignments
------------

Assignments will be split to multi lines if they don't fit together with Keyword in one line:

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Keyword
                ${first_assignment}    ${second_assignment}    Some Lengthy Keyword So That This Line Is Too Long    ${arg1}    ${arg2}

                ${first_assignment}    ${second_assignment}    ${third_assignment}    Some Lengthy Keyword So That This Line Is Too Long And Bit Over    ${arg1}    ${arg2}

    .. tab-item:: After

        .. code:: robotframework

            *** Keywords ***
            Keyword
                ${first_assignment}    ${second_assignment}    Some Lengthy Keyword So That This Line Is Too Long
                ...    ${arg1}
                ...    ${arg2}

                ${first_assignment}
                ...    ${second_assignment}
                ...    ${third_assignment}
                ...    Some Lengthy Keyword So That This Line Is Too Long And Bit Over
                ...    ${arg1}
                ...    ${arg2}

Single values
----------------

By default single values (``${variable}    value``) are not split. You can configure ``SplitTooLine`` transformer
to split on single too long values using ``split_single_value`` option::

    robocop format --configure SplitTooLongLine.split_single_value=True

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Variables ***
            &{USER_PROFILE}                   name=John Doe                            age=12                            hobby=coding
            ${SHORT_VALUE}    value
            ${SINGLE_HEADER}    veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery

    .. tab-item:: After (default)

        .. code:: robotframework

            *** Variables ***
            &{USER_PROFILE}
            ...    name=John Doe
            ...    age=12
            ...    hobby=coding
            ${SHORT_VALUE}    value
            ${SINGLE_HEADER}    veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery

    .. tab-item:: After (split_single_value = True)

        .. code:: robotframework

            *** Variables ***
            &{USER_PROFILE}
            ...    name=John Doe
            ...    age=12
            ...    hobby=coding
            ${SHORT_VALUE}    value
            ${SINGLE_HEADER}
            ...    veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery

Align new line
----------------

It is possible to align new line to previous line when splitting too long line. This mode works only when we are
filling the line until line the length limit (with one of the ``split_on_every_arg``, ``split_on_every_value`` and
``split_on_every_setting_arg`` flags). To enable it configure it using ``align_new_line``::

    > robocop format -c SplitTooLongLine.align_new_line=True

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Keywords ***
            Keyword
                [Tags]    longertagname1    longertagname2    longertagname3
                Keyword With Longer Name    ${arg1}    ${arg2}    ${arg3}    # let's assume ${arg3} does not fit under limit

    .. tab-item:: After (align_new_line = False)

        .. code:: robotframework

            *** Keywords ***
            Keyword
                [Tags]    longertagname1    longertagname2
                ...    longertagname3
                Keyword With Longer Name    ${arg1}    ${arg2}
                ...    ${arg3}

    .. tab-item:: After (align_new_line = True)

        .. code:: robotframework

            *** Keywords ***
            Keyword
                [Tags]    longertagname1    longertagname2
                ...       longertagname3
                Keyword With Longer Name    ${arg1}    ${arg2}
                ...                         ${arg3}

Ignore comments
----------------

To not count length of the comment to line length use :ref:`skip option` option::

    robocop format --configure SplitTooLongLine.skip=comments

This allows to accept and do not format lines that are longer than allowed length because of the added comment.

Skip formatting
----------------

It is possible to use the following arguments to skip formatting of the code:

- :ref:`skip option`
- :ref:`skip keyword call`
- :ref:`skip keyword call pattern`
- :ref:`skip sections`

It is also possible to use disablers (:ref:`disablers`) but ``skip`` option
makes it easier to skip all instances of given type of the code.
