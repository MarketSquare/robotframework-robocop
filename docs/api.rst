.. _api:

API
===

``robocop`` package can be imported and used directly in Python code.
You need to create instance of ``Config`` class that will contain your configuration:

..  code-block:: python
    :caption: example.py

    import robocop

    config = robocop.Config()
    config.include = {'1003'}
    config.paths = ['tests\\atest\\rules\\section-out-of-order']

``Config`` can also load configuration automatically from ``.robocop`` file if it exists in the project root:

..  code-block:: python
    :caption: example.py

    import robocop

    config = robocop.Config(root='C:\your_project\')

created ``Config`` is used to initiate ``Robocop`` class:

..  code-block:: python

    robocop_runner = robocop.Robocop(config=config)

It is recommended to reload configuration before running the checks (it should register rules and reports based on your
configuration):

..  code-block:: python

    robocop_runner.reload_config()


Scan files supplied in configuration
------------------------------------
To scan all files provided in ``Config`` invoke:

..  code-block:: python

    robocop_runner.run()

``run()`` method by default returns issues in JSON format.

Scan existing robot ast model
-----------------------------
If you have `AST <https://docs.python.org/3/library/ast.html>`_ model loaded before, you can use ``robocop`` to scan it:

..  code-block:: python

        # source is in-memory content of the file - if it is None,
        # Robocop will load content using filename path instead
        issues = robocop_runner.run_check(ast_model, filename, source)

``run_check`` returns issues in ``Message`` format (internal Robocop type).
You can find or add your own type converters to ``robocop.utils``. Currently, there is
a converter between ``Message`` and LSP diagnostic format:

..  code-block:: python

    from robocop.utils import issues_to_lsp_diagnostic

    issues = issues_to_lsp_diagnostic(issues)

