import discord
from .base import BaseRule


class MaxWordsRule(BaseRule):
    def __init__(self, config):
        super().__init__(config)
        self.name = "MaxWordsRule"

    async def get_max_words_length(self, guild: discord.Guild):
        """Method to get the max words allowed / set"""

        try:
            return await self.config.guild(guild).get_raw(self.rule_name, "max_words")
        except KeyError:
            return None

    async def set_max_words_length(self, guild: discord.Guild, max_length: int):
        """Set the max words length into config - this overrides :)"""
        await self.config.guild(guild).set_raw(self.rule_name, "max_words", value=max_length)

    async def is_offensive(self, message: discord.Message):
        content = message.content.split()
        guild = message.guild
        max_length = await self.get_max_words_length(guild)
        if not max_length:
            return False

        if len(content) >= max_length:
            return True
