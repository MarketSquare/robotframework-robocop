.. _integrations:

************
Integrations
************

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

See :ref:`gitlab` for more information about report and how to configure it.
