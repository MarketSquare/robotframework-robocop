.. _NormalizeSectionHeaderName:

NormalizeSectionHeaderName
======================================

Normalize section headers names.

.. |FORMATTERNAME| replace:: NormalizeSectionHeaderName
.. include:: enabled_hint.txt

Robot Framework is quite flexible with the section header naming. Following lines are equal::

    *setting
    *** SETTINGS
    *** SettingS ***

This transformer normalize naming to follow ``*** SectionName ***`` format (with plurar variant)::

    *** Settings ***
    *** Keywords ***
    *** Test Cases ***
    *** Variables ***
    *** Comments ***

Optional data after section header (for example data driven column names) is preserved.
It is possible to upper case section header names by passing ``uppercase=True`` parameter::

    robocop format --configure NormalizeSectionHeaderName.uppercase=True

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            * setting *

    .. tab-item:: After

        .. code:: robotframework

            *** SETTINGS ***

Skip formatting
----------------

It is possible to use the following arguments to skip formatting of the code:

- :ref:`skip sections`

It is also possible to use disablers (:ref:`disablers`) but ``skip`` option
makes it easier to skip all instances of given type of the code.
