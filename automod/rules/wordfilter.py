import discord
from .base import BaseRule

from ..utils import *
import logging

log = logging.getLogger("red.breadcogs.automod")


class WordFilterRule(BaseRule):
    def __init__(self, config):
        super().__init__(config)
        self.name = "filterword"

    async def add_to_filter(
        self,
        guild: discord.Guild,
        word: str,
        channel: discord.TextChannel = None,
        is_cleaned: bool = False,
    ) -> None:
        """
        Add a word to the filter list
        Parameters
        ----------
        word: str
            The word to filter

        channel: discord.TextChannel, Optional
            The channel where to filter

        is_cleaned: bool
            If True all punctuation will be removed from the words being checked. This defaults to False

        guild: discord.Guild
            The guild where the filtered word applies

        Returns
        -------
        None
        """
        to_append = {word: {"is_cleaned": is_cleaned, "channel": channel.id if channel else None}}
        try:
            words = await self.config.guild(guild).get_raw(self.rule_name, "words")
            words.append(to_append)
            await self.config.guild(guild).set_raw(self.rule_name, "words", value=words)
        except KeyError:
            return await self.config.guild(guild).set_raw(
                self.rule_name, "words", value=[to_append]
            )

    async def get_filtered_words(self, guild: discord.Guild) -> [dict]:
        """
        Get all the filtered words from config
        Parameters
        ----------
        guild: discord.Guild
            The guild where to fetch from config

        Returns
        -------
        A list of dicts:
            { `word`: { "is cleaned" : `bool`, "channel": `discord.TextChannel` }
        """
        try:
            words = await self.config.guild(guild).get_raw(self.rule_name, "words")
            return words
        except KeyError:
            return []

    async def is_offensive(self, message: discord.Message):
        pass
