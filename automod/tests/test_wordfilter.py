import pytest
from redbot.core import Config

from ..rules.wordfilter import WordFilterRule

word_filter_data = [
    ("Bakers do indeed bake bread", [{"word": "do", "is_cleaned": False}], True),
    ("Bakers do indeed bake bread", [{"word": "DO", "is_cleaned": False}], False),
    ("Bake,rs do ind,eed b.ake br!ead", [{"word": "do", "is_cleaned": True}], True),
    ("Bak;e;rs d,o inde.ed bake bread", [{"word": "DO", "is_cleaned": True}], False),
]


@pytest.mark.parametrize("sentence, filtered_words, expected", word_filter_data)
@pytest.mark.asyncio
async def test_filtering_words_in_sentence(sentence, filtered_words, expected):
    wordfilterrule = WordFilterRule(Config)
    assert await wordfilterrule.is_filtered(sentence, filtered_words) == expected


