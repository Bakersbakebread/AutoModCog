import discord
from .base import BaseRule

from ..utils import *

from redbot.core import commands
import logging

log = logging.getLogger("red.breadcogs.automod")


class MentionSpamRule(BaseRule):
    def __init__(self, config):
        super().__init__(config)
        self.name = "mentionspam"

    async def is_offensive(self, message: discord.Message):
        author = message.author

        try:
            mention_threshold = await self.config.guild(message.guild).get_raw(
                "settings", "mention_threshold"
            )
        except KeyError:
            mention_threshold = 4

        mention_count = sum(not m.bot and m.id != author.id for m in message.mentions)

        if mention_count >= mention_threshold:
            return True

    async def set_threshold(self, ctx, threshold):
        guild = ctx.guild
        before = 4
        try:
            before = await self.config.guild(guild).get_raw(
                "settings", "mention_threshold"
            )
        except KeyError:
            pass

        await self.config.guild(guild).set_raw(
            "settings", "mention_threshold", value=threshold
        )
        log.info(
            f"{ctx.author} ({ctx.author.id}) changed mention threshold from {before} to {threshold}"
        )
        return before, threshold
