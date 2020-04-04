from collections import defaultdict

import discord
import asyncio

from redbot.core.data_manager import bundled_data_path

from .base import BaseRule

from redbot.core import commands
import datetime


# Inspiration and some logic taken from RoboDanny
class CooldownByContent(commands.CooldownMapping):
    def _bucket_key(self, message: discord.Message,) -> tuple:
        return (
            message.channel.id,
            message.content,
        )


class SpamChecker:
    def __init__(self,):
        self.by_content = CooldownByContent.from_cooldown(15, 17.0, commands.BucketType.member,)
        self.by_user = commands.CooldownMapping.from_cooldown(10, 12.0, commands.BucketType.user,)

    def is_spamming(self, message: discord.Message,) -> bool:
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

    def __init__(self, config, bot, data_path, *args, **kwargs):
        super().__init__(config, *args, **kwargs)
        self._spam_check = defaultdict(SpamChecker)
        self.user_cache = []
        self.bot = bot
        self.data_path = data_path
        self.is_sleeping = False

    async def make_nice_file(self, list_of_ids) -> None:
        with open(f"{self.data_path}/spam_users.txt", "w") as f:
            f.write(str(datetime.date.today()))
            f.write("\n\n")
            for id in list_of_ids:
                f.write(f"{id}\n")
            f.write("--" * 10)
            f.write(f"\n{len(list_of_ids)} total users.")

    async def finish_collecting(self, message):
        if not self.is_sleeping:
            channel = await self.config.guild(message.guild).get_raw("settings", "announcement_channel")
            channel = self.bot.get_channel(channel)
            self.is_sleeping = True
            await asyncio.sleep(300)
            await self.make_nice_file(set(self.user_cache))
            await channel.send("ID's found during most recent spamrule encounter:",
                               file=discord.File(f"{self.data_path}/spam_users.txt"))


    async def is_offensive(self, message: discord.Message,) -> bool:
        checker = self._spam_check[message.guild.id]
        if not checker.is_spamming(message):
            return False

        if message.author.id not in self.user_cache:
            self.user_cache.append(message.author.id)
        await self.finish_collecting(message)

        return True
