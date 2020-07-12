import discord
from .base import BaseRule

MAX_WORDS_KEY = "max_words"


class MaxWordsRule(BaseRule):
    def __init__(
        self, config,
    ):
        super().__init__(config)
        self.name = "MaxWordsRule"

    async def get_max_words_length(
        self, guild: discord.Guild,
    ):
        """Method to get the max words allowed / set"""
        try:
            return await self.config.guild(guild).get_raw(self.rule_name, MAX_WORDS_KEY)
        except KeyError:
            return None

    async def set_max_words_length(self, guild: discord.Guild, max_length: int):
        """Set the max words length into config - this overrides :)"""
        await self.config.guild(guild).set_raw(self.rule_name, MAX_WORDS_KEY, value=max_length)

    @staticmethod
    async def message_is_max_length(message_content: str, max_length) -> bool:
        """
        Check if message word length is greater than threshold
        Parameters
        ----------
        message_content
            The message content to test
        max_length
            The upper amount of messages allowed
        """
        message_content = message_content.split()
        return len(message_content) >= max_length

    async def is_offensive(self, message: discord.Message):
        guild = message.guild
        max_length = await self.get_max_words_length(guild)
        if not max_length:
            return False

        return await self.message_is_max_length(message.content, max_length)
