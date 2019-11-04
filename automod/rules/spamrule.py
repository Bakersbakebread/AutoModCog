from collections import defaultdict

import discord
import enum

from .base import BaseRule

from redbot.core import commands
import datetime


# Inspiration and some logic taken from RoboDanny
class CooldownByContent(commands.CooldownMapping):
    def _bucket_key(self, message: discord.Message) -> tuple:
        return message.channel.id, message.content


class SpamChecker:
    def __init__(self):
        self.by_content = CooldownByContent.from_cooldown(15, 17.0, commands.BucketType.member)
        self.by_user = commands.CooldownMapping.from_cooldown(10, 12.0, commands.BucketType.user)

    def is_spamming(self, message: discord.Message) -> bool:
        current = message.created_at.replace(tzinfo=datetime.timezone.utc).timestamp()

        user_bucket = self.by_user.get_bucket(message)
        if user_bucket.update_rate_limit(current):
            return True

        content_bucket = self.by_content.get_bucket(message)
        if content_bucket.update_rate_limit(current):
            return True

        return False


class SpamRule(BaseRule):
    """
    1) It checks if a user has spammed more than 10 times in 12 seconds
    2) It checks if the content has been spammed 15 times in 17 seconds.
    """
    def __init__(self, config, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self._spam_check = defaultdict(SpamChecker)

    async def is_offensive(self, message: discord.Message) -> bool:
        checker = self._spam_check[message.guild.id]
        if not checker.is_spamming(message):
            return False

        return True


