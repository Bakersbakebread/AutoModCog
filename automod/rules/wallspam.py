from typing import Union

import discord

from .config.WallspamRuleConfig import WallspamRuleConfig
from .base import BaseRule


class WallSpamRule(BaseRule):
    def __init__(self, config):
        super().__init__(config)
        self.name = "wallspamrule"

    async def set_is_emptyline_offensive(self, guild: discord.Guild, is_enabled: bool):
        """
        Utility method to abstract config logic of setting whether to enable/disable emptline spam.
        Parameters
        ----------
        guild
            The guild where the setting is for
        is_enabled
            The bool of whether is enabled or disabled
        """
        await self.config.guild(guild).set_raw(
            self.rule_name, WallspamRuleConfig.emptyline_enabled, value=is_enabled
        )

    async def get_is_emptyline_offensive(self, guild: discord.Guild) -> bool:
        """
        Util method to abstract config logic
        Parameters
        ----------
        guild
            The guild where to get the setting for
        """
        try:
            return await self.config.guild(guild).get_raw(
                self.rule_name, WallspamRuleConfig.emptyline_enabled
            )
        except KeyError:
            # not set to we will just default to false.
            return False

    async def set_emptyline_threshold(self, guild: discord.Guild, number_of_lines: int):
        """
        Util method to abstract config logic.
        Parameters
        ----------
        guild
            The guild whose setting to set
        number_of_lines
            The number of empty lines that will be considered spam
        """
        await self.config.guild(guild).set_raw(
            self.rule_name, WallspamRuleConfig.emptyline_threshold, value=number_of_lines
        )

    async def get_emptyline_threshold(self, guild: discord.Guild) -> int:
        """
        Util method to abstract config logic
        Parameters
        ----------
        guild
            the guild to get settings from
        """
        try:
            return await self.config.guild(guild).get_raw(
                self.rule_name, WallspamRuleConfig.emptyline_threshold
            )
        except KeyError:
            # not set, default to 5
            return 5

    @staticmethod
    async def is_emptyline_spam(message_content: str, threshold: int) -> bool:
        """Detects threshold of empty new lines in message"""
        return "\n" * threshold in message_content

    @staticmethod
    async def first_character_repeating(message_content: str) -> bool:
        message_content = message_content.split()
        return len(message_content[0]) > 500

    @staticmethod
    async def is_wall_text(message_content: str) -> bool:
        message_content = message_content.split()
        return sum((item.count(message_content[0]) for item in message_content)) > 25

    async def is_offensive(
        self, message,
    ):
        try:
            is_checking_for_emptylines = await self.get_is_emptyline_offensive(message.guild)
            if is_checking_for_emptylines:
                threshold = await self.get_emptyline_threshold(message.guild)
                return await self.is_emptyline_spam(message.content, threshold)

            first_character_repeating = await self.first_character_repeating(message.content)
            is_wall_text = await self.is_wall_text(message.content)

            if is_wall_text or first_character_repeating:
                return True
        except IndexError:
            # probably one word message.
            pass
