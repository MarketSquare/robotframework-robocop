*** Settings ***
Documentation    Cell scalar ${cell    scalar}
...    Cell list @{cell    list}
...    Cell dictionary &{cell    dictionary}
...    Cell environment %{CELL    ENV}
...    Row scalar ${row
...    scalar}
...    Row list @{row
...    list}
...    Row dictionary &{row
...    dictionary}
...    Row environment %{ROW
...    ENV}
...    Escaped cell scalar \${escaped    scalar}
...    Escaped cell list \@{escaped    list}
...    Escaped cell dictionary \&{escaped    dictionary}
...    Escaped cell environment \%{ESCAPED    ENV}
...    Escaped row scalar \${escaped
...    scalar}
...    Escaped row list \@{escaped
...    list}
...    Escaped row dictionary \&{escaped
...    dictionary}
...    Escaped row environment \%{ESCAPED
...    ENV}
...    Removed continuation slash ${same}\
...    Later identical prefix ${same}\inside
