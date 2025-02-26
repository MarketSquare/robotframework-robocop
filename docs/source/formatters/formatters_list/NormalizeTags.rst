.. _NormalizeTags:

NormalizeTags
================================

Normalize tag names by normalizing case and removing duplicates.

.. |FORMATTERNAME| replace:: NormalizeTags
.. include:: enabled_hint.txt

Supported cases: lowercase (default), uppercase, title case.

You can configure case using ``case`` parameter::

    robocop format --select NormalizeTags.case=uppercase

You can remove duplicates without normalizing case by setting ``normalize_case`` parameter to False::

    robocop format --select NormalizeTags.normalize_case=False


Preserve formatting
--------------------

Tags formatting like new lines, separators or comments position will be lost when using ``NormalizeTags``
transformer. You can preserve formatting by using ``preserve_format`` flag::

    robocop format --configure NormalizeTags.preserve_format=True

The downside is that the duplications will not be removed when ``preserve_format`` is enabled.

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Test Cases ***
            Test
                [Tags]    NeedNormalization_Now    # Tell some
                ...    also_need_Normalization     # interesting story
                ...     TAG                        # about those tags

    .. tab-item:: After (default)

        .. code:: robotframework

            *** Test Cases ***
            Test
                [Tags]    neednormalization_now    also_need_normalization    tag    # Tell some    # interesting story    # about those tags

    .. tab-item:: After (preserve_format=True)

        .. code:: robotframework

            *** Test Cases ***
            Test
                [Tags]    neednormalization_now    # Tell some
                ...    also_need_normalization     # interesting story
                ...     tag                        # about those tags
