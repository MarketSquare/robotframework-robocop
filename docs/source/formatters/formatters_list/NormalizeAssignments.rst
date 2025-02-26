.. _NormalizeAssignments:

NormalizeAssignments
================================

Normalize assignments.

It can change all assignment signs to either the most commonly used in a given file or a configured one.
Default behaviour is autodetect for assignments from Keyword Calls and removing assignment signs in
``*** Variables ***`` section. It can be freely configured.

.. |FORMATTERNAME| replace:: NormalizeAssignments
.. include:: enabled_hint.txt

In this code most common is no equal sign at all. It should remove ``=`` signs from all lines:

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Variables ***
            ${var} =  ${1}
            @{list}  a
            ...  b
            ...  c

            ${variable}=  10


            *** Keywords ***
            Keyword
                ${var}  Keyword1
                ${var}   Keyword2
                ${var}=    Keyword

    .. tab-item:: After

        .. code:: robotframework

            *** Variables ***
            ${var}  ${1}
            @{list}  a
            ...  b
            ...  c

            ${variable}  10


            *** Keywords ***
            Keyword
                ${var}  Keyword1
                ${var}   Keyword2
                ${var}    Keyword

You can configure that behaviour to automatically add desired equal sign with ``equal_sign_type``
(default ``autodetect``) and ``equal_sign_type_variables`` (default ``remove``) parameters.
(possible types are: ``autodetect``, ``remove``, ``equal_sign`` ('='), ``space_and_equal_sign`` (' =')::

    robocop format -c NormalizeAssignments.equal_sign_type=space_and_equal_sign -c NormalizeAssignments.equal_sign_type_variables=autodetect

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Variables ***
            ${var}=  ${1}
            @{list}  a
            ...  b
            ...  c

            ${variable}=  10


            *** Keywords ***
            Keyword
                ${var}  Keyword1
                ${var}   Keyword2
                ${var}=    Keyword

    .. tab-item:: After

        .. code:: robotframework

            *** Variables ***
            ${var}=  ${1}
            @{list}=  a
            ...  b
            ...  c

            ${variable}=  10


            *** Keywords ***
            Keyword
                ${var} =  Keyword1
                ${var} =   Keyword2
                ${var} =    Keyword

Skip formatting
----------------

It is possible to use the following arguments to skip formatting of the code:

- :ref:`skip sections`

It is also possible to use disablers (:ref:`disablers`) but ``skip`` option
makes it easier to skip all instances of given type of the code.
