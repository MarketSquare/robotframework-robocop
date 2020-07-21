User guide
==========
This is short overview on how to use Robocop together with links to more extensive documentation.

You can run lint scan on Robot Framework code by simply running::

    robocop path/to/file/files

Robocop accept files or directories as path. You can also specify multiple paths::

    robocop file.robot resources/etc test.robot

Including or excluding rules
----------------------------

Rules can be included or excluded from command line. It is also possible to disable rule(s) from Robot Framework
source code. More in :ref:`including-rules`.

Format output message
---------------------

Format of output messages can be redefined. More in messages documentation: :ref:`messages`.

Configuring rules
-----------------

Rules are configurable. Severity of every rule message can be changed and also some of the rules have
optional parameters. More on this in :ref:`checkers`.

Save output to file
-------------------

You can redirect output of Robocop to a file by using pipes (``>`` in unix) or by ``-o`` / ``--output`` argument::

  robocop --output robocop.log



Generating reports
------------------

You can generate reports after run. Available reports are described in :ref:`reports`.