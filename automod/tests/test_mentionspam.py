import pytest

from ..rules.mentionspam import MentionSpamRule

THRESHOLD = 1
BREAD_MENTION = "<@280730525960896513>"
FAKE_MENTION = "<@280730525960896511>"

test_data = [
    # empty allowed_mentions
    ("This is a sentence", [], THRESHOLD, False),
    (f"{BREAD_MENTION} This is a sentence", [], THRESHOLD, True),
    (f"{FAKE_MENTION} This is a sentence", [], THRESHOLD, True),
    (f"{BREAD_MENTION} {BREAD_MENTION} This is a sentence", [], THRESHOLD, True),
    (f"{BREAD_MENTION} This is a sentence", [BREAD_MENTION], THRESHOLD, False),
    (f"{FAKE_MENTION} This is a sentence", [BREAD_MENTION], THRESHOLD, True),
    (f"{FAKE_MENTION} {BREAD_MENTION} This is a sentence", [BREAD_MENTION], THRESHOLD, True),
    (f"{BREAD_MENTION} {BREAD_MENTION} This is a sentence", [BREAD_MENTION], THRESHOLD, False),
]


@pytest.mark.parametrize("message_content, allowed_mentions, threshold, expected", test_data)
@pytest.mark.asyncio
async def test_mentions_greater_than_threshold(
    message_content, allowed_mentions, threshold, expected
):
    assert (
        await MentionSpamRule.mentions_greater_than_threshold(
            message_content, allowed_mentions, threshold
        )
        == expected
    )
