import discord

from .base import BaseRule

MAX_CHARS_KEY = "max_chars"


class MaxCharsRule(BaseRule):
    def __init__(
        self, config,
    ):
        super().__init__(config)

    async def set_max_chars_length(self, guild: discord.Guild, max_length: int):
        await self.config.guild(guild).set_raw(self.rule_name, MAX_CHARS_KEY, value=max_length)

    async def get_max_chars(self, guild: discord.Guild):
        try:
            return await self.config.guild(guild).get_raw(self.rule_name, MAX_CHARS_KEY)
        except KeyError:
            return None

    @staticmethod
    async def message_is_max_chars(message_content: str, threshold: int):
        return len(message_content) >= threshold

    async def is_offensive(self, message: discord.Message):
        max_chars = await self.get_max_chars(message.guild)

        if max_chars is None:
            return False

        return await self.message_is_max_chars(message.content, max_chars)
