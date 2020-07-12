import pytest

from ..rules.maxchars import MaxCharsRule

THRESHOLD = 5


test_data = [
    ("This is a sentence", THRESHOLD, True),
    ("This is", THRESHOLD, True),
    ("12345", THRESHOLD, True),
    ("1234", THRESHOLD, False),
]


@pytest.mark.parametrize("message_content, threshold, expected", test_data)
@pytest.mark.asyncio
async def test_message_is_max_length(message_content, threshold, expected):
    assert await MaxCharsRule.message_is_max_chars(message_content, threshold) == expected
