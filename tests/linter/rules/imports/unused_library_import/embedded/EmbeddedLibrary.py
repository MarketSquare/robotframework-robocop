from robot.api.deco import keyword


@keyword("Add ${number} to ${other_number}")
def add(number, other_number):
    return int(number) + int(other_number)
