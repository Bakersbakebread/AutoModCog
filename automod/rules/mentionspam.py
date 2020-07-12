import discord
from .base import BaseRule

from ..utils import *
import logging
import re

log = logging.getLogger("red.breadcogs.automod")


class MentionSpamRule(BaseRule):
    def __init__(
        self, config,
    ):
        super().__init__(config)
        self.name = "mentionspam"

    @staticmethod
    async def mentions_greater_than_threshold(
        message_content: str, allowed_mentions: [str], threshold: int
    ):
        content_filtered = [
            word for word in message_content.split() if word not in allowed_mentions
        ]
        mention = re.compile(r"<@!?(\d+)>")
        mention_count = len(list(filter(mention.match, content_filtered)))
        return mention_count >= threshold

    async def is_offensive(
        self, message: discord.Message,
    ):
        try:
            mention_threshold = await self.config.guild(message.guild).get_raw(
                "settings", "mention_threshold",
            )
        except KeyError:
            mention_threshold = 4

        allowed_mentions = [message.author.mention]
        return await self.mentions_greater_than_threshold(
            message.content, allowed_mentions, mention_threshold
        )

    async def set_threshold(
        self, ctx, threshold,
    ):
        guild = ctx.guild
        before = 4
        try:
            before = await self.config.guild(guild).get_raw("settings", "mention_threshold",)
        except KeyError:
            pass

        await self.config.guild(guild).set_raw(
            "settings", "mention_threshold", value=threshold,
        )
        log.info(
            f"{ctx.author} ({ctx.author.id}) changed mention threshold from {before} to {threshold}"
        )
        return (
            before,
            threshold,
        )
