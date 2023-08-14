Rule severity threshold and global threshold filter (#930)
-----------------------------------------------------------

Rule that uses configured severity threshold (which can dynamically set rule severity) will no longer be filtered out
by global threshold ``-t/--threshold`` if rule default severity is lower than configured threshold.

For example, given rule ``file-too-long`` which has default Warning severity and following configuration::

    robocop -c file-too-long:severity_threshold:warning=600:error=700 -t E .

If file has more than 700 lines it should be reported as Error and not be filtered out by ``--threshold``.
