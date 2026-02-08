from enum import Enum

_VAR_PREFIXES = ("${", "@{", "&{", "%{")


class StringPart(Enum):
    MASKED = "masked"
    UNMASKED = "unmasked"


def map_string_to_mask(s: str) -> list[tuple[str, StringPart]]:
    """
    Map string to mask/unmask to make it possible to ignore part of strings in further processing.

    Part of string that are enclosed with ', " or are Robot variables (${var}) are masked.

    Returns:
        list of tuple pairs: string part and MASKED/UNMASKED enum value.

    """
    if "'" not in s and '"' not in s and "{" not in s:
        return [(s, StringPart.UNMASKED)]
    n = len(s)
    i = 0

    out = []
    buf_start = 0

    while i < n:
        # Variable block handling (outside quotes only)
        for p in _VAR_PREFIXES:
            if s.startswith(p, i):
                out.append((s[buf_start:i], StringPart.UNMASKED))

                depth = 1
                j = i + 2
                # find & ignore nested variables
                while j < n and depth:
                    for np in _VAR_PREFIXES:
                        if s.startswith(np, j):
                            depth += 1
                            j += 2
                            break
                    else:
                        if s[j] == "}":
                            depth -= 1
                        j += 1
                # check for ${var}['item']
                if j < n and s[j] == "[":
                    bracket_end = s.find("]", j + 1)
                    if bracket_end != -1:
                        j = bracket_end + 1
                out.append((s[i:j], StringPart.MASKED))
                i = j
                buf_start = i
                break
        if i >= n:
            break
        ch = s[i]

        # Quote handling
        if ch == "'":
            quote_end = s.find("'", i + 1)
            if quote_end != -1:
                out.append((s[buf_start:i], StringPart.UNMASKED))
                out.append((s[i : quote_end + 1], StringPart.MASKED))
                i = quote_end + 1
                buf_start = i
                continue
        if ch == '"':
            quote_end = s.find('"', i + 1)
            if quote_end != -1:
                out.append((s[buf_start:i], StringPart.UNMASKED))
                out.append((s[i : quote_end + 1], StringPart.MASKED))
                i = quote_end + 1
                buf_start = i
                continue
        i += 1

    # remaining part
    if buf_start < n:
        out.append((s[buf_start:], StringPart.UNMASKED))

    return out


def get_unmasked_string(value: str) -> str:
    """Return string with masked parts removed."""
    return "".join(part for part, part_type in map_string_to_mask(value) if part_type == StringPart.UNMASKED)
