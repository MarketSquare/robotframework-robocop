*** Keywords ***
Exclude whole multiline case by rule "Should_Not_Be_None"
    Should_Not_Be_None      ${NIMIKEKUVAUS}   ${HINTA_OCC_ULKOINEN}   ${MITTAYKSIKKÖ}  ${NIMIKETYYPPI_OCC}  ${OSANUMERO}
    ...                     ${NIMIKE}  ${MÄÄRÄ}   ${MITTAYKSIKKÖ}   ${LÄHETYSOSOITE_OCC}   ${LASKUTUSOSOITE_OCC}

    Should Be None    ${VALUE}

    Should Contain Word    ${VALUE}

    Prefix_starts_with    ${VALUE}
    ...    ${VALUE}

    not_prefix_starts_with    ${ARG}

    ${HINTA_YKSI}  ${HINTA_RIVI}  ${HINTA_TILAUS_ALV}  ${toimituspvm}=
    ...                     TiHa_MyyntitilausTarkista_Tiedot
    ...                     ${TILAUS_FUSION}            ${NIMIKE}           ${NIMIKEKUVAUS}     ${MÄÄRÄ}            ${MITTAYKSIKKÖ}     ${TILAUSPVM}
    ...                     ${ASIAKAS}                  ${ASIAKAS_ID}       ${LÄHETYSOSOITE}    ${LÄHETYSTAPA}      ${LASKUTUSOSOITE}
    ...                     ${LIIKEYKSIKKÖ}             ${TILAAJA}          tila_tilaus=Käsittelyssä                tila_tilausrivi=Odottaa lähetystä
    ...                     lähde=${LÄHDE}              hinta_yks=${HINTA_YKSI}                 hinta_rivi=${HINTA_RIVI}

    ${HINTA_YKSI}  ${HINTA_RIVI}  ${HINTA_TILAUS_ALV}  ${toimituspvm}    TiHa_MyyntitilausTarkista_Tiedot
