*** Variables ***
# Simple type.
${version: float}         7.3
# Parameterized type.
${CRITICAL: list[int]}    [3278, 5368, 5417]
# With @{list} variables the type specified the item type.
@{HIGH: int}              4173    5334    5386    5387
@{HIGH low: int}              4173    5334    5386    5387
# With @{dict} variables the type specified the value type.
&{DATes: date}            rc1=2025-05-08    final=2025-05-15
# Alternative syntax to specify both key and value types.
&{NUMBERS: int=float}     1=2.3    4=5.6
