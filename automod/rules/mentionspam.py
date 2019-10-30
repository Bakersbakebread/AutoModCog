import discord
from .base import BaseRule

from ..utils import *

from redbot.core import commands


class MentionSpamRule(BaseRule):
    def __init__(self, config):
        super().__init__(config)
        self.name = "mentionspam"

    async def is_offensive(self, message: discord.Message):
        author = message.author

        try:
            mention_threshold = await self.config.guild(message.guild).get_raw("settings", "mention_threshold")
        except KeyError:
            mention_threshold = 4

        mention_count = sum(not m.bot and m.id != author.id for m in message.mentions)

        if mention_count >= mention_threshold:
            return True