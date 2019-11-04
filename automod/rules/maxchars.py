import discord

from .base import BaseRule

class MaxCharsRule(BaseRule):
    def __init__(self, config):
        super().__init__(config)

    async def set_max_chars_length(self, guild: discord.Guild, max_length: int):
        await self.config.guild(guild).set_raw(self.rule_name, "max_chars", value=max_length)

    async def get_max_chars(self, guild: discord.Guild):
        try:
            return await self.config.guild(guild).get_raw(self.rule_name, "max_chars")
        except KeyError:
            return None

    async def is_offensive(self, message: discord.Message):
        content = message.content
        max_chars = await self.get_max_chars(message.guild)

        if max_chars is None:
            return False

        if len(content) >= max_chars:
            return True
