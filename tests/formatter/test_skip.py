import re
from unittest.mock import Mock

import pytest

from robocop.formatter.skip import Skip, SkipConfig


class TestSkip:
    @pytest.mark.parametrize(("keyword_call", "str_keyword_call"), [({"test", "keyword"}, "test,keyword")])
    @pytest.mark.parametrize(("return_values", "str_return_values"), [(True, "True"), (False, "False")])
    @pytest.mark.parametrize(("doc", "str_doc"), [(True, "True"), (False, "False")])
    def test_from_str_cfg(self, doc, str_doc, return_values, str_return_values, keyword_call, str_keyword_call):
        skip_config_from_str = SkipConfig()
        skip_config_from_str.update_with_str_config(
            documentation=str_doc,
            return_values=str_return_values,
            keyword_call=str_keyword_call,
        )
        skip = set()
        if doc:
            skip.add("documentation")
        if return_values:
            skip.add("return_values")
        skip_config = SkipConfig(skip=skip, keyword_call=keyword_call)
        assert skip_config_from_str == skip_config

    @pytest.mark.parametrize(
        ("skip_keyword", "names", "disabled"),
        [
            ("executejavascript", ["Execute Javascript"], [True]),
            ("executejavascript", ["OtherLib.Execute Javascript"], [False]),
            ("executejavascript", ["Keyword"], [False]),
            ("Execute_Javascript", ["Keyword", "Execute_Javas cript"], [False, True]),
            ("executejavascript", [None], [False]),
            (
                "executejavascript,otherkeyword",
                ["Execute Javascript", "Test Keyword", "Other_keyword"],
                [True, False, True],
            ),
        ],
    )
    def test_skip_keyword_call(self, skip_keyword, names, disabled):
        mock_node = Mock()
        skip_config = SkipConfig()
        skip_config.update_with_str_config(keyword_call=skip_keyword)
        skip = Skip(skip_config=skip_config)
        for name, disable in zip(names, disabled):
            mock_node.keyword = name
            assert disable == skip.keyword_call(mock_node)

    @pytest.mark.parametrize(
        ("skip_keyword", "names", "disabled"),
        [
            ("Execute Javascript", ["Execute Javascript"], [True]),
            ("Execute Javascript", ["executejavascript"], [False]),
            (r"(?i)execute\s?javascript", ["Execute Javascript"], [True]),
            ("executejavascript", ["Keyword"], [False]),
            ("Javascript", ["Execute Javascript"], [True]),
            ("^Javascript", ["Execute Javascript"], [False]),
            ("Execute", ["Execute Javascript"], [True]),
            ("Execute1", ["Execute Javascript"], [False]),
            ("Execute", ["Execute Javascript", "Execute Other Stuff", "Keyword"], [True, True, False]),
            (
                r"(?i)Library\.",
                ["Library.Stuff", "Library2.Stuff", "library.Other_stuff", "library"],
                [True, False, True, False],
            ),
            ("(?i)execute,javascript", ["Execute", "Quasadilla", "Javascript"], [True, False, False]),
            ("executejavascript", [None], [False]),
        ],
    )
    def test_skip_keyword_call_pattern(self, skip_keyword, names, disabled):
        mock_node = Mock()
        skip_config = SkipConfig()
        skip_config.update_with_str_config(keyword_call_pattern=skip_keyword)
        skip = Skip(skip_config=skip_config)
        for name, disable in zip(names, disabled):
            mock_node.keyword = name
            assert disable == skip.keyword_call(mock_node)

    def test_keyword_call_pattern_invalid(self):
        invalid_regex = "[0-9++"
        skip_config = SkipConfig(keyword_call_pattern={invalid_regex})
        msg_error = re.escape(f"'{invalid_regex}' is not a valid regular expression.")
        with pytest.raises(ValueError, match=msg_error):
            Skip(skip_config=skip_config)

    def test_global_local_skip_documentation(self):
        # local overrides global
        skip_config = SkipConfig()
        skip_config.update_with_str_config(documentation="True")
        assert "documentation" in skip_config.skip

    def test_global_local_keyword_call(self):
        # list are joined
        skip_config = SkipConfig(keyword_call={"name", "name2"})
        skip_config.update_with_str_config(keyword_call="name,name3")
        assert skip_config.keyword_call == {"name", "name2", "name3"}

    def test_only_global_return_values(self):
        # global takes precedence
        skip_config = SkipConfig(skip={"return_values"})
        skip_config.update_with_str_config()
        assert "return_values" in skip_config.skip
