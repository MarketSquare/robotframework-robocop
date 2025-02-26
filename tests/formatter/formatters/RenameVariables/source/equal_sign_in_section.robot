*** Variables ***
${random_seed} =    ${None}


*** Keywords ***
Keyword With Sign
    ${value} =  Keyword Call    ${random_seed}
