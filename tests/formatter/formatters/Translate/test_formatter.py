from tests.formatter import FormatterAcceptanceTest


class TestTranslate(FormatterAcceptanceTest):
    FORMATTER_NAME = "Translate"

    # FIXME After integrating, test is unstable - something wrong with language settings
    # @pytest.mark.parametrize("source_lang", [["pl"], ["pl", "de"]])  # ["en"],
    # @pytest.mark.parametrize("dest_lang", ["de", "en"])  # , "pl"
    # def test_translation(self, source_lang, dest_lang):
    #     configure = []
    #     language = None
    #     if dest_lang != "en":
    #         configure.append(f"{self.FORMATTER_NAME}.language={dest_lang}")
    #     if source_lang != ["en"]:
    #         language = source_lang
    #     source_file = "_and_".join(source_lang) + ".robot"
    #     not_modified = source_lang == [dest_lang]
    #     self.compare(
    #         configure=configure,
    #         language=language,
    #         source=source_file,
    #         expected=f"{dest_lang}.robot",
    #         not_modified=not_modified,
    #     )

    def test_recognize_language_header(self):  # FIXME language header not recognized
        self.compare(
            configure=[f"{self.FORMATTER_NAME}.language=en"],
            language=["pl"],
            source="pl_language_header.robot",
            expected="en_with_pl_header.robot",
        )

    def test_bdd(self):
        configure = [
            f"{self.FORMATTER_NAME}.language=pl",
            f"{self.FORMATTER_NAME}.translate_bdd=True",
        ]
        self.compare(
            configure=configure,
            language=["pl"],
            source="bdd/en_and_pl.robot",
            expected="bdd/pl.robot",
        )
        configure = [
            f"{self.FORMATTER_NAME}.language=uk",
            f"{self.FORMATTER_NAME}.translate_bdd=True",
        ]
        self.compare(
            configure=configure,
            language=["pl"],
            source="bdd/en_and_pl.robot",
            expected="bdd/uk.robot",
        )

    def test_bdd_alternative(self):
        configure = [
            f"{self.FORMATTER_NAME}.language=pl",
            f"{self.FORMATTER_NAME}.translate_bdd=True",
            f"{self.FORMATTER_NAME}.given_alternative=Zakładając",
        ]
        self.compare(
            configure=configure,
            language=["pl"],
            source="bdd/en_and_pl.robot",
            expected="bdd/pl_alternative.robot",
        )

    # def test_bdd_alternative_invalid(self):  TODO check error output
    # from robocop.formatter.utils.misc import ROBOT_VERSION
    #     if ROBOT_VERSION.major < 6:
    #         pytest.skip("Test enabled only for RF 6.0+")
    #     configure = [
    #         f"{self.FORMATTER_NAME}.language=pl",
    #         f"{self.FORMATTER_NAME}.translate_bdd=True",
    #         f"{self.FORMATTER_NAME}.but_alternative=chyba",
    #     ]
    #     result = self.run_tidy(
    #         select=[self.FORMATTER_NAME],
    #         configure=configure,
    #         language=["pl"],
    #         source="bdd/en_and_pl.robot",
    #         exit_code=1,
    #     )
    #     expected_output = (
    #         f"Error: {self.FORMATTER_NAME}: Invalid 'but_alternative' parameter value: 'chyba'. "
    #         "Provided BDD keyword alternative does not exist in the destination language. Select one of: Ale\n"
    #     )
    #     assert expected_output == result.output

    def test_add_language_header(self):
        configure = [
            f"{self.FORMATTER_NAME}.language=pl",
            f"{self.FORMATTER_NAME}.add_language_header=True",
        ]
        self.compare(
            configure=configure,
            source="add_lang_header/empty.robot",
            expected="add_lang_header/empty.robot",
            not_modified=True,
        )
        self.compare(
            configure=configure,
            source="add_lang_header/comment_section.robot",
            expected="add_lang_header/comment_section.robot",
        )
        self.compare(
            configure=configure,
            source="add_lang_header/diff_lang_header.robot",
            expected="add_lang_header/diff_lang_header.robot",
        )
        self.compare(
            configure=configure,
            source="add_lang_header/no_lang_header.robot",
            expected="add_lang_header/no_lang_header.robot",
        )
        self.compare(
            configure=[f"{self.FORMATTER_NAME}.add_language_header=True"],
            source="add_lang_header/en_header.robot",
            expected="add_lang_header/en_header.robot",
        )
