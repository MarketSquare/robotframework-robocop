User guide
==========
This is short overview of how to use Robocop together with links to more extensive documentation.

You can run lint scan on Robot Framework code by simply running::

    robocop path/to/file/files

Robocop accepts files or directories as path. You can also specify multiple paths::

    robocop file.robot resources/etc test.robot

Including or excluding rules
----------------------------

Rules can be included or excluded from command line. It is also possible to disable rule(s) from Robot Framework
source code. More in :ref:`including-rules`.

Ignoring file
-------------
Path matching glob pattern can be ignored (or *skipped* during scan). You can pass list of patterns::

    robocop --ignore *.robot,resources/* --ignore special_file.txt

Format output message
---------------------

Format of rules output messages can be redefined. More in messages documentation: :ref:`rules`.

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

Return status
-------------

Return status of Robocop depends on number of issues reported per given severity level. Default levels are following::

  quality_gate = {
            'E': 1,
            'W': 100,
            'I': -1
        }

Number -1 means that return status is not affected by number of issues for given message. Default values can be configured
by ``-c/--configure`` and ``return_status:quality_gate`` param::

  robocop --configure return_status:quality_gate:E=100:F=10:I=9

Preceding example configuration results in following levels::

  quality_gate = {
            'E': 100,
            'W': 100,
            'I': 9
        }

Any number of *Error* issues above or equal 100, *Warning* above or equal 100 and *Info* above or equal 9
will lead to Robocop returning status code (1).