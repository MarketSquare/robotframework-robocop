---
name: Bug report
about: File a bug report
title: '[Bug] '
labels: 'bug'
assignees: ''
body:
  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
      description: Also tell us, what did you expect to happen?
      value: ""
    validations:
      required: true
  - type: checkboxes
    id: version
    attributes:
      label: Version
      description: Do you use latest version of Robocop?
      options:
        - label: Yes
        - label: No
    validations:
      required: true
  - type: markdown
  attributes:
    value: |
      Thanks for your report!
---