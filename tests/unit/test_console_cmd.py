"""Unit tests related console application."""
import pytest
from console.cmd import get_params


@pytest.mark.parametrize(
    "input, expected_text",
    [("""clean      up  abc """, "clean-up-abc"),
     ("""clean "up"   abc """, "clean-up-abc")]
)
def test_console_cmd(input, expected_text):
    """Make sure the message is parsed correctly."""

    output = get_params(input)
    assert isinstance(output, list)
    expected_list = expected_text.split('-')
    for i in range(0, len(output)):
        assert output[i] == expected_list[i]
