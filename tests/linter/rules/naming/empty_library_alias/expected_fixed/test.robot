*** Settings ***
Resources    library.py
Library      Collections
Library      other_library.py  # comment
Library      other_library.py    WITH NAME  PrettyName  # comment
Library      other_library.py
Library      other_library.py    AS    SomeName
Library      WITH NAME
Library      other_library.py     arg=1    AS     MyName
Library      other_library.py     arg=1
