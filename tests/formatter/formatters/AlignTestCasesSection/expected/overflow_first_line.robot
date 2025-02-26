*** Test Cases ***
compact_overflow issue case
    ${HINTA_YKSI}           ${HINTA_RIVI}               ${HINTA_TILAUS_ALV}    ${toimituspvm}=
    ...                     TiHa_MyyntitilausTarkista_Tiedot
    ...                     ${TILAUS_FUSION}            ${NIMIKE}           ${NIMIKEKUVAUS}     ${MÄÄRÄ}            ${MITTAYKSIKKÖ}     ${TILAUSPVM}
    ...                     ${ASIAKAS}                  ${ASIAKAS_ID}       ${LÄHETYSOSOITE}    ${LÄHETYSTAPA}      ${LASKUTUSOSOITE}
    ...                     ${LIIKEYKSIKKÖ}             ${TILAAJA}          tila_tilaus=Käsittelyssä    tila_tilausrivi=Odottaa lähetystä
    ...                     lähde=${LÄHDE}              hinta_yks=${HINTA_YKSI}    hinta_rivi=${HINTA_RIVI}

    RaAn_RaporttiTarkista_REP98
    ...                     70 Procurement              RPOR LOG Ostoa odottavat rivit (REP98).xdo    HTML          ${LUONTIYKSIKKÖ}
    ...                     ${LIIKEYKSIKKÖ}             ${TOIMITTAJA}       ${TOIMITTAJAN_TOIMIPAIKKA}    ${ASIAKASTYYPPI}    ${NIMIKETYYPPI}

compact_overflow OK working case
    Set Library Search Order    QWeb                    QMobile
