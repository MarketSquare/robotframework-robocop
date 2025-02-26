.. _formatters:

Formatters list
===============

.. toctree::
    :hidden:
    :maxdepth: 1
    :glob:

    *

.. rubric:: List of formatters

To see list of all formatters currently implemented in `robocop format` run:

.. code:: shell

    robocop format --list

Formatters are sorted in the order they are run by default.

# TODO
To see description of the transformer run:

.. code:: shell

    robocop format --desc TRANSFORMER_NAME

See :ref:`configuring-formatters` to learn how formatters can be configured (including disabling and enabling formatters).

.. rubric:: Order of formatters

By default all formatters run in the same order. Whether called with:

.. code:: shell

   robocop format

or:

.. code:: shell

   robocop format --select ReplaceRunKeywordIf --select SplitTooLongLine

or:

.. code:: shell

   robocop format --select SplitTooLongLine --select ReplaceRunKeywordIf

It will transform files according to internal order (in this example ``ReplaceRunKeywordIf`` is before
``SplitTooLongLine``). To see order of the formatters run ``robocop format --list``.

If you want to transform files using different transformer order you need to run formatters separately:

.. code:: shell

   robocop format --select SplitTooLongLine
   robocop format --select ReplaceRunKeywordIf

You can also add ``--force-order`` flag to use order provided in cli:

.. code:: shell

   robocop format --force-order --select SplitTooLongLine --select ReplaceRunKeywordIf

External formatters are used last. If you want to change this behaviour (for example run your custom transformer
before default ones) you need to use ``--force-order`` flag.

.. rubric:: Pipe handling

Not all formatters can handle pipe syntax. If you encounter any issues with pipe separators, run
``NormalizeSeparators`` transformer to replace pipes with spaces.
