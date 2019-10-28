import discord
from redbot.core.commands import command, commands
import logging

from .utils import transform_bool

log = logging.getLogger(name="red.breadcogs.automod")

class Settings:

    async def set_announcement_channel(self, guild: discord.Guild, channel: discord.TextChannel) -> tuple:
        """Sets the channel where announcements should be sent"""
        before_channel = None
        try:
            before = await self.config.guild(guild).get_raw("settings", "announcement_channel")
            before_channel = guild.get_channel(before)
        except KeyError:
            pass

        await self.config.guild(guild).set_raw("settings", "announcement_channel", value=channel.id)

        return before_channel, channel

    async def toggle_announcements(self, guild: discord.Guild):
        before = None
        try:
            before = await self.config.guild(guild).get_raw("settings", "is_announcement_enabled")
        except KeyError:
            pass

        if before is None:
            before = True

        await self.config.guild(guild).set_raw("settings", "is_announcement_enabled", value = not before)

        return before, not before

    @commands.group()
    async def announce(self, ctx):
        """Change the announcement settings"""
        pass

    @announce.command(name="enable")
    async def _enable(self, ctx):
        """
        Toggles sending announcement messages on infractions
        """
        before, after = await self.toggle_announcements(ctx.guild)

        log.info(f"{ctx.author} ({ctx.author.id}) toggled announcements from {before} to {after}")
        await ctx.send(f"`🔔` Announcements changed from `{transform_bool(before)}` to `{transform_bool(after)}`")

    @announce.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        """
        Set the channel where announcements should be posted.

        """
        before, after = await self.set_announcement_channel(ctx.guild, channel)

        log.info(
            f"{ctx.author} ({ctx.author.id}) changed announcement channel from {before} {before.id or ' '} to {after} {after.id}"
        )
        await ctx.send(f"`🔔` Announcement channel changed from `{before}` to `{after}`")