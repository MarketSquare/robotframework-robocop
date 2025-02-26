language: de
*** Kommentare ***
Hallo liebe Teilnehmenden,

Das ist eine Detsche Suite.


*** Einstellungen ***
Bibliothek      String


*** Variablen ***
${Redner}       René Rohner


*** Testfälle ***
Testfall 1
    [Tags]    marker1    marker2
    [Vorbereitung]    Log To Console    Das ist der Anfang
    Sag mal    Hallo
    Log    Bitte das hier auch in die Console    console=Ja
    Log To Console    Das ist mitten drin
    [Nachbereitung]    Log To Console    Das ist das Ende


*** Schlüsselwörter ***
Sag mal
    [Argumente]    ${Nachricht}
    Log    ${Nachricht}    html=ja
