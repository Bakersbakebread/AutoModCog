import discord
from .base import BaseRule
import re

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
        author: discord.Member,
        channels: [discord.TextChannel] = None,
        is_cleaned: bool = False,
    ) -> None:
        """
        Add a word to the filter list
        Parameters
        ----------
        word: str
            The word to filter

        author: discord.Member
            The person who added the word to the filter

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
        to_append = {
            "word": word,
            "author": author.id,
            "is_cleaned": is_cleaned,
            "channel": [channel.id for channel in channels] if channels else [],
        }
        try:
            words = await self.config.guild(guild).get_raw(self.rule_name, "words")
            words.append(to_append)
            await self.config.guild(guild).set_raw(self.rule_name, "words", value=words)
        except KeyError:
            return await self.config.guild(guild).set_raw(
                self.rule_name, "words", value=[to_append]
            )

    async def remove_filter(self, guild: discord.Guild, word: str) -> None:
        """
        Removes a word from the list of filtered words
        Parameters
        ----------
        guild: discord.Guild
            The guild where the word is
        word
            The word to remove
        Returns
        -------
            None

        Raises
        -------
            ValueError if word is not found
        """
        all_words = await self.get_filtered_words(guild)
        for index, word_dict in enumerate(all_words):
            if word.lower() == word_dict["word"]:
                all_words.pop(index)

        await self.config.guild(guild).set_raw(self.rule_name, "words", value=all_words)

    async def get_filtered_words(self, guild: discord.Guild) -> [dict]:
        """
        Get all the filtered words from config
        Parameters
        ----------
        guild: discord.Guild
            The guild where to fetch from config

        Returns
        -------
        A list of dicts
        """
        try:
            words = await self.config.guild(guild).get_raw(self.rule_name, "words")
            return words
        except KeyError:
            return []

    @staticmethod
    def remove_punctuation(sentence: str):
        from string import punctuation

        no_punc = sentence.translate(str.maketrans("", "", punctuation))
        return no_punc

    @staticmethod
    def no_mentions(sentence: str):
        mentionless = re.sub(r"<@!?(\d+)>", "", sentence)
        return mentionless

    async def is_filtered(self, sentence: str, filtered_words: [dict]):
        for word in filtered_words:
            to_filter = word["word"]
            is_cleaned = word["is_cleaned"]

            if is_cleaned:
                sentence = self.remove_punctuation(sentence)

            if to_filter in sentence:
                return True

        return False

    async def is_offensive(self, message: discord.Message):
        all_words = await self.get_filtered_words(message.guild)
        sentence = self.no_mentions(message.content)

        for word in all_words:
            channels = word["channel"]
            if message.channel.id in channels or channels is None:
                return await self.is_filtered(sentence, all_words)
