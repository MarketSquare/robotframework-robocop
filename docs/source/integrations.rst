.. _integrations:

************
Integrations
************

pre-commit
----------

To use Robocop as `pre-commit <https://pre-commit.com/>`_ hook, you need following ``.pre-commit-config.yaml`` file::

    - repo: https://github.com/MarketSquare/robotframework-robocop
      # Robocop version.
      rev: 6.0
      hooks:
        # Run the linter.
        - id: robocop
        # Run the formatter.
        - id: robocop-format

It will run both linter and formatter on your modified files when trying to commit changes. If any linter issue is
found or file is modified, it will stop the commit.

Gitlab
------

You can integrate Robocop results with `Gitlab Code Quality <https://docs.gitlab.com/ci/testing/code_quality/#implement-a-custom-tool>`_ .

For that purpose you need to generate report that supports Code Quality format::

    robocop check --reports gitlab

It's also available using ``--gitlab`` option::

    robocop check --gitlab

By default it will produce ``robocop-code-quality.json`` file in the directory where Robocop was executed.
You will need to attach this file to Gitlab artifacts::

    stages:
      - lint

    robocop:
      stage: lint
      image: python:3.12
      before_script:
        - pip install robotframework-robocop==6.0
      script:
        - robocop check --gitlab
      artifacts:
        reports:
          codequality: robocop-code-quality.json

See :ref:`gitlab` for more information about the report and how to configure it.

Sonar Qube
----------

Robocop results can be imported into Sonar Qube with `generic formatted result <https://docs.sonarsource.com/sonarqube-server/latest/analyzing-source-code/importing-external-issues/generic-issue-import-format/>`_ .

Such report can be generated with ``sonarqube`` report::

    robocop check --reports sonarqube

By default it will produce ``robocop_sonar_qube.json`` file in the directory where Robocop was executed.
You will need to attach this file in the CI/CD by defining analysis parameter ``sonar.externalIssuesReportPaths``.

See :ref:`sonarqube` for more information about the report and how to configure it.
