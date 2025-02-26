*** Ustawienia ***
Biblioteka    python.py
Dokumentation    This is doc

Ukończenie Zestawu    Keyword

Znaczniki Zadania    tag


*** Variablen ***
${VAR}    ${TRUE}


*** Testfälle ***
Pierwszy test
    [Vorbereitung]
    [Znaczniki]
    Słowo kluczowe

Dokumentacja
    [Dokumentation]    This is doc
    No Operation

*** Słowa Kluczowe ***
Keyword
    [Argumenty]    ${arg}
    IF    $condition
        Log    ${arg}
    ELSE
        BREAK
    END
