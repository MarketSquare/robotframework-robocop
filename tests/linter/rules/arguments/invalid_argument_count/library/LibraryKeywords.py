"""Library used to test that keywords from libraries are validated."""


class LibraryKeywords:
    def keyword_with_arguments(self, first, second="default"):
        pass

    def keyword_without_arguments(self):
        pass

    def keyword_with_varargs(self, first, *rest):
        pass

    def keyword_with_named_only(self, first, *, strict):
        pass
