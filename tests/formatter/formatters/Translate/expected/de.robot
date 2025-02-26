*** Einstellungen ***
Bibliothek    python.py
Dokumentation    This is doc

Suitenachbereitung    Keyword

Aufgabenmarker    tag


*** Variablen ***
${VAR}    ${TRUE}


*** Testfälle ***
Pierwszy test
    [Vorbereitung]
    [Marker]
    Słowo kluczowe

Dokumentacja
    [Dokumentation]    This is doc
    No Operation

*** Schlüsselwörter ***
Keyword
    [Argumente]    ${arg}
    IF    $condition
        Log    ${arg}
    ELSE
        BREAK
    END
