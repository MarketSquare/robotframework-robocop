Python 3.12 support (#968 #969)
--------------------------------

Fixes related to Python 3.12 support:

- escaped variables and special variable syntax (such as ``$variable``) should now work with Python 3.12 and variable
  rules like ``unused-variable`` or ``unused-argument``
- Robocop should not print code warnings from not properly escaped docstrings anymore
