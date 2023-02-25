import collections
import itertools
import re
from functools import total_ordering
from typing import List, Optional, SupportsInt, Tuple, Union

VERSION_PATTERN = r"""
    v?
    (?:
        (?P<release>[0-9]+(?:\.[0-9]+)*)                  # release segment
        (?P<pre>                                          # pre-release
            [-_\.]?
            (?P<pre_l>(a|b|c|rc|alpha|beta|pre|preview))
            [-_\.]?
            (?P<pre_n>[0-9]+)?
        )?
        (?P<dev>                                          # dev release
            [-_\.]?
            (?P<dev_l>dev)
            [-_\.]?
            (?P<dev_n>[0-9]+)?
        )?
    )
    (?:\+(?P<local>[a-z0-9]+(?:[-_\.][a-z0-9]+)*))?       # local version
"""


class InfinityType:
    def __lt__(self, other: object) -> bool:
        return False

    def __le__(self, other: object) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__)

    def __gt__(self, other: object) -> bool:
        return True

    def __ge__(self, other: object) -> bool:
        return True

    def __neg__(self: object) -> "NegativeInfinityType":
        return NegativeInfinity


class NegativeInfinityType:
    def __lt__(self, other: object) -> bool:
        return True

    def __le__(self, other: object) -> bool:
        return True

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__)

    def __gt__(self, other: object) -> bool:
        return False

    def __ge__(self, other: object) -> bool:
        return False

    def __neg__(self: object) -> InfinityType:
        return Infinity


Infinity = InfinityType()
NegativeInfinity = NegativeInfinityType()


def _get_comparison_key(
    release: Tuple[int, ...],
    pre: Optional[Tuple[str, int]],
    dev: Optional[Tuple[str, int]],
):
    # When we compare a release version, we want to compare it with all the
    # trailing zeros removed. So we'll use a reverse the list, drop all the now
    # leading zeros until we come to something non zero, then take the rest
    # re-reverse it back into the correct order and make it a tuple and use
    # that for our sorting key.
    _release = tuple(reversed(list(itertools.dropwhile(lambda x: x == 0, reversed(release)))))

    # We need to "trick" the sorting algorithm to put 1.0.dev0 before 1.0a0.
    # We'll do this by abusing the pre segment, but we _only_ want to do this
    # if there is not a pre segment. Otherwise, the normal sorting rules will handle this case correctly.
    if pre is None and dev is not None:
        _pre = NegativeInfinity
    # Versions without a pre-release (except as noted above) should sort after
    # those with one.
    elif pre is None:
        _pre = Infinity
    else:
        _pre = pre

    # Versions without a development segment should sort after those with one.
    _dev = Infinity if dev is None else dev
    return _release, _pre, _dev


def _parse_letter_version(letter: str, number: Union[str, bytes, SupportsInt]) -> Optional[Tuple[str, int]]:
    if letter:
        # We consider there to be an implicit 0 in a pre-release if there is
        # not a numeral associated with it.
        if number is None:
            number = 0

        # We normalize any letters to their lower case form
        letter = letter.lower()

        if letter == "alpha":
            letter = "a"
        elif letter == "beta":
            letter = "b"
        elif letter in ["c", "pre", "preview"]:
            letter = "rc"

        return letter, int(number)
    return None


@total_ordering
class Version:
    _version_pattern = re.compile(rf"^\s*{VERSION_PATTERN}\s*$", re.VERBOSE | re.IGNORECASE)

    def __init__(self, version: str) -> None:
        match = self._version_pattern.search(version)
        self.release = tuple(int(i) for i in match.group("release").split("."))
        self.pre = _parse_letter_version(match.group("pre_l"), match.group("pre_n"))
        self._dev = _parse_letter_version(match.group("dev_l"), match.group("dev_n"))
        self._key = _get_comparison_key(
            self.release,
            self.pre,
            self._dev,
        )

    def __lt__(self, other) -> bool:
        return self._key < other._key

    def __eq__(self, other) -> bool:
        return self._key == other._key

    def __str__(self) -> str:
        parts = [".".join(str(x) for x in self.release)]
        if self.pre is not None:
            parts.append("".join(str(x) for x in self.pre))

        if self.dev is not None:
            parts.append(f".dev{self.dev}")

        return "".join(parts)

    @property
    def dev(self) -> Optional[int]:
        return self._dev[1] if self._dev else None

    @property
    def public(self) -> str:
        return str(self).split("+", 1)[0]

    @property
    def base_version(self) -> str:
        parts = [".".join(str(x) for x in self.release)]
        return "".join(parts)

    @property
    def is_prerelease(self) -> bool:
        return self.dev is not None or self.pre is not None

    @property
    def major(self) -> int:
        return self.release[0] if len(self.release) >= 1 else 0

    @property
    def minor(self) -> int:
        return self.release[1] if len(self.release) >= 2 else 0

    @property
    def micro(self) -> int:
        return self.release[2] if len(self.release) >= 3 else 0


def _pad_version(left, right):
    left_split, right_split = [], []

    # Get the release segment of our versions
    left_split.append(list(itertools.takewhile(lambda x: x.isdigit(), left)))
    right_split.append(list(itertools.takewhile(lambda x: x.isdigit(), right)))

    # Get the rest of our versions
    left_split.append(left[len(left_split[0]) :])
    right_split.append(right[len(right_split[0]) :])

    # Insert our padding
    left_split.insert(1, ["0"] * max(0, len(right_split[0]) - len(left_split[0])))
    right_split.insert(1, ["0"] * max(0, len(left_split[0]) - len(right_split[0])))

    return (list(itertools.chain(*left_split)), list(itertools.chain(*right_split)))


_prefix_regex = re.compile(r"^([0-9]+)((?:a|b|c|rc)[0-9]+)$")


def _version_split(version: str):
    result: List[str] = []
    for item in version.split("."):
        match = _prefix_regex.search(item)
        if match:
            result.extend(match.groups())
        else:
            result.append(item)
    return result


def _is_not_suffix(segment: str) -> bool:
    return not any(segment.startswith(prefix) for prefix in ("dev", "a", "b", "rc"))


class VersionSpecifier:
    _regex_str = r"""
        (?P<operator>(~=|==|!=|<=|>=|<|>))
        (?P<version>
            (?:
                # The (non)equality operators allow for wild card and local
                # versions to be specified so we have to define these two
                # operators separately to enable that.
                (?<===|!=)            # Only match for equals and not equals

                \s*
                v?
                [0-9]+(?:\.[0-9]+)*   # release
                (?:                   # pre release
                    [-_\.]?
                    (a|b|c|rc|alpha|beta|pre|preview)
                    [-_\.]?
                    [0-9]*
                )?
                # You cannot use a wild card and a dev or local version
                # together so group them with a | and make them optional.
                (?:
                    (?:[-_\.]?dev[-_\.]?[0-9]*)?         # dev release
                    (?:\+[a-z0-9]+(?:[-_\.][a-z0-9]+)*)? # local
                    |
                    \.\*  # Wild card syntax of .*
                )?
            )
            |
            (?:
                # The compatible operator requires at least two digits in the
                # release segment.
                (?<=~=)               # Only match for the compatible operator

                \s*
                v?
                [0-9]+(?:\.[0-9]+)+   # release  (We have a + instead of a *)
                (?:                   # pre release
                    [-_\.]?
                    (a|b|c|rc|alpha|beta|pre|preview)
                    [-_\.]?
                    [0-9]*
                )?
                (?:[-_\.]?dev[-_\.]?[0-9]*)?          # dev release
            )
            |
            (?:
                # All other operators only allow a sub set of what the
                # (non)equality operators do. Specifically they do not allow
                # local versions to be specified nor do they allow the prefix
                # matching wild cards.
                (?<!==|!=|~=)         # We have special cases for these
                                      # operators so we want to make sure they
                                      # don't match here.

                \s*
                v?
                [0-9]+(?:\.[0-9]+)*   # release
                (?:                   # pre release
                    [-_\.]?
                    (a|b|c|rc|alpha|beta|pre|preview)
                    [-_\.]?
                    [0-9]*
                )?
                (?:[-_\.]?dev[-_\.]?[0-9]*)?          # dev release
            )
        )
        """

    _regex = re.compile(r"^\s*" + _regex_str + r"\s*$", re.VERBOSE | re.IGNORECASE)

    _operators = {
        "~=": "compatible",
        "==": "equal",
        "!=": "not_equal",
        "<=": "less_than_equal",
        ">=": "greater_than_equal",
        "<": "less_than",
        ">": "greater_than",
    }

    def __init__(self, spec: str = "") -> None:
        match = self._regex.search(spec)
        if not match:
            raise ValueError(f"Invalid specifier: '{spec}'")

        self._spec: Tuple[str, str] = (
            match.group("operator").strip(),
            match.group("version").strip(),
        )

    def __contains__(self, item: str) -> bool:
        normalized_item = self._coerce_version(item)

        operator_callable = self._get_operator(self.operator)
        return operator_callable(normalized_item, self.version)

    def _coerce_version(self, version):
        if not isinstance(version, Version):
            version = Version(version)
        return version

    def _get_operator(self, op: str):
        operator_callable = getattr(self, f"_compare_{self._operators[op]}")
        return operator_callable

    @property
    def operator(self) -> str:
        return self._spec[0]

    @property
    def version(self) -> str:
        return self._spec[1]

    def _compare_compatible(self, prospective, spec: str) -> bool:
        # Compatible releases have an equivalent combination of >= and ==. That
        # is that ~=2.2 is equivalent to >=2.2,==2.*. This allows us to
        # implement this in terms of the other specifiers instead of
        # implementing it ourselves. The only thing we need to do is construct
        # the other specifiers.

        # We want everything but the last item in the version, but we want to
        # ignore suffix segments.
        prefix = ".".join(list(itertools.takewhile(_is_not_suffix, _version_split(spec)))[:-1])

        # Add the prefix notation to the end of our string
        prefix += ".*"

        return self._get_operator(">=")(prospective, spec) and self._get_operator("==")(prospective, prefix)

    def _compare_equal(self, prospective, spec: str) -> bool:
        if spec.endswith(".*"):
            # In the case of prefix matching we want to ignore local segment.
            prospective = Version(prospective.public)
            # Split the spec out by dots, and pretend that there is an implicit
            # dot in between a release segment and a pre-release segment.
            split_spec = _version_split(spec[:-2])  # Remove the trailing .*

            # Split the prospective version out by dots, and pretend that there
            # is an implicit dot in between a release segment and a pre-release
            # segment.
            split_prospective = _version_split(str(prospective))

            # Shorten the prospective version to be the same length as the spec
            # so that we can determine if the specifier is a prefix of the
            # prospective version or not.
            shortened_prospective = split_prospective[: len(split_spec)]

            # Pad out our two sides with zeros so that they both equal the same
            # length.
            padded_spec, padded_prospective = _pad_version(split_spec, shortened_prospective)

            return padded_prospective == padded_spec
        else:
            # Convert our spec string into a Version
            spec_version = Version(spec)
            return prospective == spec_version

    def _compare_not_equal(self, prospective, spec: str) -> bool:
        return not self._compare_equal(prospective, spec)

    def _compare_less_than_equal(self, prospective, spec: str) -> bool:
        return Version(prospective.public) <= Version(spec)

    def _compare_greater_than_equal(self, prospective, spec: str) -> bool:
        return Version(prospective.public) >= Version(spec)

    def _compare_less_than(self, prospective, spec_str: str) -> bool:
        spec = Version(spec_str)
        if not prospective < spec:
            return False
        if not spec.is_prerelease and prospective.is_prerelease:
            return Version(prospective.base_version) != Version(spec.base_version)
        return True

    def _compare_greater_than(self, prospective, spec_str: str) -> bool:
        return prospective <= Version(spec_str)
