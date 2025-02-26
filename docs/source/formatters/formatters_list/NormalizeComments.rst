.. _NormalizeComments:

NormalizeComments
================================

Normalize comments.

.. |FORMATTERNAME| replace:: NormalizeComments
.. include:: enabled_hint.txt

Normalizes spacing after the beginning of the comment. Fixes ``missing-space-after-comment`` rule violations
from the Robocop.

.. tab-set::

    .. tab-item:: Before

        .. code:: robotframework

            *** Settings ***
            #linecomment
            ### header


            *** Keywords ***
            Keyword
                Step  #comment

    .. tab-item:: After

        .. code:: robotframework

            *** Settings ***
            # linecomment
            ### header


            *** Keywords ***
            Keyword
                Step  # comment

Skip formatting
----------------

It is possible to use the following arguments to skip formatting of the code:

- :ref:`skip option` (``--skip comments``)
