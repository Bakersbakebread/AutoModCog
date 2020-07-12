import pytest

from ..rules.maxwords import MaxWordsRule

THRESHOLD = 3


test_data = [
    ("This is a sentence", THRESHOLD, True),
    ("This is", THRESHOLD, False),
]


@pytest.mark.parametrize("message_content, threshold, expected", test_data)
@pytest.mark.asyncio
async def test_message_is_max_length(message_content, threshold, expected):
    assert await MaxWordsRule.message_is_max_length(message_content, threshold) == expected
