language: pl

*** Ustawienia ***
Biblioteka    python.py
Dokumentacja    This is doc

Ukończenie Zestawu    Keyword

Znaczniki Zadania    tag


*** Zmienne ***
${VAR}    ${TRUE}


*** Przypadki Testowe ***
Pierwszy test
    [Inicjalizacja]
    [Znaczniki]
    Słowo kluczowe

Dokumentacja
    [Dokumentacja]    This is doc
    No Operation

*** Słowa Kluczowe ***
Keyword
    [Argumenty]    ${arg}
    IF    $condition
        Log    ${arg}
    ELSE
        BREAK
    END
