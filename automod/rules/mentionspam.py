import discord
from .base import BaseRule

from ..utils import *

from redbot.core import commands
import logging
import re

log = logging.getLogger("red.breadcogs.automod")


class MentionSpamRule(BaseRule):
    def __init__(self, config):
        super().__init__(config)
        self.name = "mentionspam"

    async def is_offensive(self, message: discord.Message):
        author = message.author
        content = message.content.split()

        try:
            mention_threshold = await self.config.guild(message.guild).get_raw(
                "settings", "mention_threshold"
            )
        except KeyError:
            mention_threshold = 4

        mention = re.compile(r"<@!?(\d+)>")
        allowed_mentions = [author.mention]
        filter_content = [x for x in content if x not in allowed_mentions]

        mention_count = len(list(filter(mention.match, filter_content)))

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
