.. _OrderSettingsSection:

OrderSettingsSection
================================

Order settings inside ``*** Settings ***`` section.

.. |FORMATTERNAME| replace:: OrderSettingsSection
.. include:: enabled_hint.txt

Settings are grouped in following groups:

- documentation (Documentation, Metadata),
- imports (Library, Resource, Variables),
- settings (Suite Setup and Teardown, Test Setup and Teardown, Test Timeout, Test Template),
- tags (Force Tags, Default Tags)

Then ordered by groups (according to ``group_order = documentation,imports,settings,tags`` order). Every
group is separated by ``new_lines_between_groups = 1`` new lines.
Settings are ordered inside group. Default order can be modified through following parameters:

- ``documentation_order = documentation,metadata``
- ``imports_order = preserved`` (default - see :ref:`imports-order` section to how configure it)
- ``settings_order = suite_setup,suite_teardown,test_setup,test_teardown,test_timeout,test_template``

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***
            Metadata  value  param

            Force Tags  tag
            ...  tag

            Documentation  doc  # this is comment
            ...  another line
            Test Timeout  1min

            # I want to be keep together with Test Setup

            Test Setup  Keyword


            Suite Setup  Keyword
            Default Tags  1
            Suite Teardown  Keyword2

            Variables   variables.py
            Library  Stuff
            Library  Collections
            Resource    robot.resource
            Library  stuff.py  WITH NAME  alias

    .. tab-item:: After

        .. code:: robotframework

            *** Settings ***
            Documentation  doc  # this is comment
            ...  another line
            Metadata  value  param

            Variables   variables.py
            Library  Stuff
            Library  Collections
            Resource    robot.resource
            Library  stuff.py  WITH NAME  alias

            Suite Setup  Keyword
            Suite Teardown  Keyword2
            # I want to be keep together with Test Setup
            Test Setup  Keyword
            Test Timeout  1min

            Force Tags  tag
            ...  tag
            Default Tags  1

Using the same example with non default group order we will move tags from end to beginning of the section::

    robocop format --configure OrderSettingsSection.group_order=tags,documentation,imports,settings

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***
            Metadata  value  param

            Force Tags  tag
            ...  tag

            Documentation  doc  # this is comment
            ...  another line
            Test Timeout  1min

            # I want to be keep together with Test Setup

            Test Setup  Keyword


            Suite Setup  Keyword
            Default Tags  1
            Suite Teardown  Keyword2

    .. tab-item:: After

        .. code:: robotframework

            *** Settings ***
            Force Tags  tag
            ...  tag
            Default Tags  1

            Documentation  doc  # this is comment
            ...  another line
            Metadata  value  param

            Suite Setup  Keyword
            Suite Teardown  Keyword2
            # I want to be keep together with Test Setup
            Test Setup  Keyword
            Test Timeout  1min

Settings order
---------------

Order of settings inside common group can also be changed::

    robocop format --configure OrderSettingsSection.settings_order=suite_teardown,suite_setup,test_setup,test_teardown,test_timeout,test_template

.. tab-set::

    .. tab-item:: Default order

        .. code:: robotframework

            *** Settings ***
            Suite Setup    Suite Setup Keyword
            Suite Teardown    Suite Teardown Keyword
            Test Timeout    1min

    .. tab-item:: Configured order

        .. code:: robotframework

            *** Settings ***
            Suite Teardown    Suite Teardown Keyword
            Suite Setup    Suite Setup Keyword
            Test Timeout    1min

Preserve order
--------------

If you want to preserve order of the settings inside the group you can use ``preserved`` value::

    robocop format --configure OrderSettingsSection.settings_order=preserved
    robocop format --configure OrderSettingsSection.documentation_order=preserved

Imports are preserved by default.

 .. _imports-order:

Imports order
--------------

By default order of the imports is preserved. You can overwrite this behaviour::

    robocop format --configure OrderSettingsSection.imports_order=library,resource,variables

With preceding configuration `robocop format` will put library imports first, then resources and variables last.
Builtin library imports are moved to the top and sorted alphabetically.

Example:

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***
            Suite Teardown  Keyword2

            Variables   variables.py
            Library  Stuff
            Library  Collections
            Resource    robot.resource
            Library   ABC

    .. tab-item:: After

        .. code:: robotframework

            *** Settings ***
            Library  Collections
            Library  Stuff
            Library   ABC
            Resource    robot.resource
            Variables   variables.py

            Suite Teardown  Keyword2

Removing settings
------------------

Setting names omitted from custom order will be removed from the file. In following example we are missing metadata
therefore all metadata will be removed::

    robocop format --configure OrderSettingsSection.documentation_order=documentation

Empty lines between group of settings
--------------------------------------

Group of settings are separated by ``new_lines_between_groups = 1`` new lines. It can be configured::

    robocop format --configure OrderSettingsSection.new_lines_between_groups=2

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***
            Library  Collections
            Default Tags    tag
            Documentation  doc  # this is comment
            ...  another line
            Metadata  value  param

    .. tab-item:: Default separator

        .. code:: robotframework

            *** Settings ***
            Documentation  doc  # this is comment
            ...  another line
            Metadata  value  param

            Library  Collections

            Default Tags    tag

    .. tab-item:: 0

        .. code:: robotframework

            *** Settings ***
            Documentation  doc  # this is comment
            ...  another line
            Metadata  value  param
            Library  Collections
            Default Tags    tag

    .. tab-item:: 2

        .. code:: robotframework

            *** Settings ***
            Documentation  doc  # this is comment
            ...  another line
            Metadata  value  param


            Library  Collections


            Default Tags    tag

If you're not preserving the default order of libraries they will be grouped into built in libraries and custom libraries.
Parsing errors (such as Resources instead of Resource, duplicated settings) are moved to the end of section.

.. tab-set::

    .. tab-item:: Before

        .. code:: none

            *** Settings ***
            Test Templating  Template  # parsing error
            Library  Stuff
            Resource    robot.resource
            Library  Dialogs  # built in library

    .. tab-item:: After

        .. code:: none

            *** Settings ***
            Library  Dialogs  # built in library
            Library  Stuff
            Resource    robot.resource

            Test Templating  Template  # parsing error
