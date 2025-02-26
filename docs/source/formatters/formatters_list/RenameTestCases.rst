.. _RenameTestCases:

RenameTestCases
================================

Enforce test case naming. This transformer capitalizes first letter of test case name removes trailing dot and
strips leading/trailing whitespaces. If ``capitalize_each_word`` is ``True``, will capitalize each word in test case name.

.. |FORMATTERNAME| replace:: RenameTestCases
.. include:: disabled_hint.txt

It is also possible to configure ``replace_pattern`` parameter to find and replace regex pattern. Use ``replace_to``
to set a replacement value. This configuration::

    robocop format --select RenameTestCases -c RenameTestCases.replace_pattern=[A-Z]{3,}-\d{2,} -c RenameTestCases.replace_to=foo

replaces all occurrences of given pattern with string 'foo':

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Test Cases ***
            test ABC-123
                No Operation

    .. tab-item:: After

        .. code:: robotframework

            *** Test Cases ***
            Test foo
                No Operation

Capitalize each word
------------------------

If you set ``capitalize_each_word`` to ``True`` it will capitalize each word in the test case name::

     robocop format --select RenameTestCases -c RenameTestCases.capitalize_each_word=True

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Test Cases ***
            compare XML with json
                No Operation

    .. tab-item:: After

        .. code:: robotframework

            *** Test Cases ***
            Compare XML With Json
                No Operation
