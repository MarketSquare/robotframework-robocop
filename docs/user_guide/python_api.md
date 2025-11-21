# Python API Reference

Robocop uses ``typer`` to create CLI. Its design makes it easy to reuse the same method exposed as CLI commands
directly in your own code.

See ``src/robocop/run.py`` to see Robocop entrypoint and methods used. The following sections describe some of the most
important methods.

## Lint code

You can lint the code from the Python application using ``check_files`` method:

```python
from robocop.run import check_files


check_files()
```

It will behave similarly as CLI command (scan results will be printed to stdout etc.). You can change the configuration
to adjust its behaviour:

```python
from robocop.run import check_files


check_files(ignore_file_config=True, return_result=True, silent=True)
```

- ``ignore_file_config`` will disable automatic loading of configuration files
- ``return_result`` will return the result object (list of diagnostics) instead of exiting the application with the exit code
- ``silent`` will disable printing of any output to stdout

See the signature of the method to find out more about available options.

## Format code

You can format the code from the Python application using ``check_files`` method. Similarly to linting, you can change
the configuration to adjust its behaviour:

```python
from robocop.run import format_files


format_files(ignore_file_config=True, return_result=True, silent=True)
```
