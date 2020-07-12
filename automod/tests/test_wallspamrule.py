import pytest
from redbot.core import Config

from ..rules.wallspam import WallSpamRule

first_character_repeating_data = [
    ("1" * 501, True),
    ("1" * 400, False),
    ("1", False),
    ("1 2", False),
]

wall_text_data = [
    ("Wallspam Wallspam " * 100, True),
    ("Wallspam Wallspam " * 10, False),
    ("Wallspam Wallspam " * 25, True),
    ("Wallspam Wallspam " * 30, True),
]


@pytest.mark.parametrize("message_content, expected", first_character_repeating_data)
@pytest.mark.asyncio
async def test_wallspam_first_character_repeating(message_content, expected):
    """Test for repeated first character, usually emojis."""
    assert await WallSpamRule.first_character_repeating(message_content) == expected


@pytest.mark.parametrize("message_content, expected", wall_text_data)
@pytest.mark.asyncio
async def test_is_wall_text(message_content, expected):
    assert await WallSpamRule.is_wall_text(message_content) == expected
