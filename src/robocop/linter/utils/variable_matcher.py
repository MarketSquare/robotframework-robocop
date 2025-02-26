from robot.variables.search import VariableMatch, search_variable

try:
    from robot.variables import VariableMatches
except ImportError:
    from collections.abc import Iterator, Sequence

    class VariableMatches:
        def __init__(self, string: str, identifiers: Sequence[str] = "$@&%", ignore_errors: bool = False):
            self.string = string
            self.identifiers = identifiers
            self.ignore_errors = ignore_errors

        def __iter__(self) -> Iterator[VariableMatch]:
            remaining = self.string
            while True:
                match = search_variable(remaining, self.identifiers, self.ignore_errors)
                if not match:
                    break
                remaining = match.after
                yield match

        def __len__(self) -> int:
            return sum(1 for _ in self)

        def __bool__(self) -> bool:
            try:
                next(iter(self))
            except StopIteration:
                return False
            else:
                return True
