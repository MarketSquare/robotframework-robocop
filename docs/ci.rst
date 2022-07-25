.. _ci:

Continous Integration support
=========================================

You can use Robocop in CI/CD from any provider using generated reports or output file.

If there is no direct support for the Robocop, you can raise an issue to add support for it
(in our `issue tracker <https://github.com/MarketSquare/robotframework-robocop/issues>`_) or implement your own solution.

One of the important configuration for CI integration is return status.
See the `docs <https://robocop.readthedocs.io/en/stable/user_guide.html#return-status>`_.

Github Code Scanning
----------------------
You can integrate Robocop results with Github Code Scanning (`Github documentation <https://docs.github.com/en/code-security/code-scanning/automatically-scanning-your-code-for-vulnerabilities-and-errors/about-code-scanning>`_).
It is possible using SARIF (Static Analysis Results Interchange Format) output format. Example below shows Github Workflow that runs the Robocop
with ``sarif`` report and uses produced file to upload results to Github Code Scanning::

    name: Run Robocop

    on:
      pull_request:
        branches: [ master ]

    jobs:
      build:
        runs-on: ubuntu-latest
        # continue even if Robocop returns issues and fails step
        continue-on-error: true
        permissions:
          # required for issues to be recorded
          security-events: write
        steps:
          - name: Checkout repository
            uses: actions/checkout@v3
          - name: Install dependencies
            run: |
              python -m pip install --upgrade pip
              pip install robotframework-robocop
          - name: Run robocop
            run: python -m robocop --reports sarif .
          - name: Upload SARIF file
            uses: github/codeql-action/upload-sarif@v2
            with:
              sarif_file: .sarif.json
              category: robocop

The Robocop issues will be recorded in Github project:

.. image:: images/github_code_scanning1.png
  :alt: Code Scanning in PR


Issue details:

.. image:: images/github_code_scanning2.png
  :alt: Code Scanning issue details

You can configure the Robocop using cli or configuration file (:ref:`configuration file`).

Jenkins
----------
There is no direct support for Robocop in the Jenkins. But it is possible to use existing plugins for tools like
pylint with Robocop output.
You can start from generating Robocop output in the file (using ``-o / --output`` option). This file can be
processed by `Warnings Next Generation plugin <https://plugins.jenkins.io/warnings-ng/>`_ to integrate Robocop
results in your pipeline. More details can be found `here <https://github.com/jenkinsci/warnings-ng-plugin/blob/master/doc/Documentation.md#creating-support-for-a-custom-tool>`_.
