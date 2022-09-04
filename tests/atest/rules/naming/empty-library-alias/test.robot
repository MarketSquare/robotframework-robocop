*** Settings ***
Resources    library.py
Library      Collections    WITH NAME
Library      other_library.py    WITH NAME  # comment
Library      other_library.py    WITH NAME  PrettyName  # comment
Library      other_library.py    AS
Library      WITH NAME