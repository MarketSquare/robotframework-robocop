*** Variables ***
${RANDOM_SEED} =    ${None}


*** Keywords ***
Keyword With Sign
    ${value} =  Keyword Call    ${RANDOM_SEED}
