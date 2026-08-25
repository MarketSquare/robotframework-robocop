from robocop.project.definitions import ArgumentsSpec


class TestArgumentsSpec:
    def test_no_arguments(self):
        spec = ArgumentsSpec.from_arguments([])
        assert spec.min_args == 0
        assert spec.max_args == 0
        assert not spec.accepts_named

    def test_positional_and_defaults(self):
        spec = ArgumentsSpec.from_arguments(["${a}", "${b}=2"])
        assert spec.positional == ("a", "b")
        assert spec.min_args == 1
        assert spec.max_args == 2

    def test_var_positional(self):
        spec = ArgumentsSpec.from_arguments(["${a}", "@{rest}"])
        assert spec.min_args == 1
        assert spec.max_args is None
        assert spec.var_positional == "rest"

    def test_var_named(self):
        spec = ArgumentsSpec.from_arguments(["${a}", "&{kwargs}"])
        assert spec.accepts_named
        assert spec.var_named == "kwargs"

    def test_named_only(self):
        spec = ArgumentsSpec.from_arguments(["@{}", "${named}"])
        assert spec.named_only == ("named",)

    def test_invalid_arguments_do_not_raise(self):
        spec = ArgumentsSpec.from_arguments(["${a}=1", "${b}"])
        assert isinstance(spec, ArgumentsSpec)
