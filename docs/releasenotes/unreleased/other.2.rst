 --ignore-git-dir option to ignore .git when searching for configuration file (#908)
------------------------------------------------------------------------------------

When searching for the default configuration file, Robocop stop searching if ``.git`` directory is found. It is now
possible to disable this behaviour using ``--ignore-git-dir`` flag.
