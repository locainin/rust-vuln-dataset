import pytest

from Verification.verifier.rust.tokens import tokenize


def check_character_literals_are_not_lifetimes():
    tokens = tokenize("'a'")

    assert len(tokens) == 1
    assert tokens[0].text == "'a'"


@pytest.mark.parametrize("text", ['"', "'", '"escaped\\"'])
def check_unclosed_literals_fail(text):
    with pytest.raises(ValueError, match="unterminated Rust literal"):
        tokenize(text)


def check_lifetimes_keep_their_names():
    assert [token.text for token in tokenize("'a 'static '_")] == [
        "'a",
        "'static",
        "'_",
    ]
