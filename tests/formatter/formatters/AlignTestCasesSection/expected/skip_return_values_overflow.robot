*** Test Cases ***
Skip return values test
    # bug when return value is exactly as long as the column:
    ${additional_tab_value}=    Create List             Tuotekuvaus         Implantoitava tuote

    # similar bug with -1 width:
    ${additional_tab_valu}=    Create List              Tuotekuvaus         Implantoitava tuote

    IF  '${varastosaldo}' != '0' or '${toimitusmäärä}' != '0' or '${kysynnänmäärä}' != '0'
        ${TILAUS_OSTO_AVOIN}    ${HANKINTAEHDOTUS_AVOIN}    ${DUMMY}            ${TILAUS_AVOIN_OCC}=    RaAn_Raportti_AvoinTilausTarkista    ${NIMIKE}
    END
