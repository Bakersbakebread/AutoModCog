import asyncio
from typing import Optional, Union

import discord
from redbot.core.commands import commands, CommandError, Converter, BadArgument
from redbot.core import checks
import logging

from redbot.core.utils.chat_formatting import box

from .rules.base import BaseRuleSettingsDisplay
from .utils import transform_bool, error_message
from .converters import ToggleBool
log = logging.getLogger(name="red.breadcogs.automod")


class Settings:
    def __init__(self, *args, **kwargs):
        self.bot = kwargs.get("bot")
        self.config = kwargs.get('config')
        self.rules_map = kwargs.get("rules_map")

    async def set_announcement_channel(
        self, guild: discord.Guild, channel: discord.TextChannel
    ) -> tuple:
        """Sets the channel where announcements should be sent"""
        before_channel = None
        try:
            before = await self.config.guild(guild).get_raw("settings", "announcement_channel")
            before_channel = guild.get_channel(before)
        except KeyError:
            pass

        await self.config.guild(guild).set_raw(
            "settings", "announcement_channel", value=channel.id
        )

        return before_channel, channel

    async def announcements_enabled(self, guild: discord.Guild) -> tuple:
        enabled = False
        channel = None
        try:
            enabled = await self.config.guild(guild).get_raw("settings", "is_announcement_enabled")
            channel = await self.config.guild(guild).get_raw("settings", "announcement_channel")
        except KeyError:
            pass

        return enabled, channel

    async def toggle_announcements(self, guild: discord.Guild, toggle: ToggleBool):
        before = False
        try:
            before = await self.config.guild(guild).get_raw("settings", "is_announcement_enabled")
        except KeyError:
            pass

        await self.config.guild(guild).set_raw(
            "settings", "is_announcement_enabled", value=toggle
        )

        return before, toggle

    async def get_all_settings(self, guild: discord.Guild) -> [discord.Embed]:
        settings = []
        for rule_name, rule in self.rules_map.items():
            settings.append(await rule.get_settings(guild))
        return settings

    async def get_rule_setting(
        self, guild: discord.Guild, rule_name: str
    ) -> [BaseRuleSettingsDisplay]:
        rule = self.rules_map.get(rule_name)
        return await rule.get_settings(guild)

    async def get_settings_to_embeds(self, settings: [BaseRuleSettingsDisplay]) -> [discord.Embed]:
        embeds = []
        setting: BaseRuleSettingsDisplay
        for setting in settings:
            guild = self.bot.get_guild(setting.guild_id)
            embed = discord.Embed(
                title=setting.rule_name,
                description=(
                    f"```ini\n"
                    f"Enabled   :   [{setting.is_enabled}]\n"
                    f"Deleting  :   [{setting.is_deleting}]\n"
                    f"---\n"
                    f"Action    :   {setting.action_to_take}  \n"
                    f"```"
                ),
            )
            if not setting.is_enabled:
                embeds.append(embed)
                continue

            enforced_value = "`Global`"
            if setting.enforced_channels:
                enforced_value = ", ".join(setting.enforced_channels)

            embed.add_field(name="Enforced Channels", value=enforced_value)
            if setting.whitelisted_roles:
                roles = []
                for r in setting.whitelisted_roles:
                    roles.append(guild.get_role(r).name)
                whitelist_value = ", ".join("`{0}`".format(w) for w in roles)
            else:
                whitelist_value = "No roles whitelisted."

            embed.add_field(name="Whitelisted Roles", value=whitelist_value)

            if setting.muted_role:
                role = guild.get_role(setting.muted_role)
                embed.add_field(name="Muted role", value=f"`{role}`", inline=False)
            embeds.append(embed)
        return embeds

    async def get_all_settings_as_embeds(self, guild):
        settings = await self.get_all_settings(guild)
        setting: BaseRuleSettingsDisplay
        embed = discord.Embed(
            title="⚙ AutoMod settings",
            description=f"For a more detailed view of an individual rule: `[p]automodset show <rule_name>`.\n",
        )
        for index, setting in enumerate(settings, 1):
            value = "```diff\n"
            if setting.is_enabled:
                value += "+ Enabled\n"
            else:
                value += "- Disabled\n"
            if setting.is_deleting:
                value += "+ Deleting\n"
            else:
                value += "-Not deleting\n"
            value += f"---Action---\n{setting.action_to_take}"
            value += "```"
            embed.add_field(name=setting.rule_name, value=value)

        announcing, where = await self.announcements_enabled(guild)
        announcing = "+ Enabled" if announcing else None
        where = (
            f"+ {guild.get_channel(where)}"
            if where
            else "- No channel has been set up to receive announcements"
        )

        embed.add_field(name="Announcing", value=box(announcing or "- Disabled", "diff"))
        if announcing:
            embed.add_field(name="Channel", value=box(where, "diff"))
        return [embed]

    async def get_rule_settings_as_embed(self, guild, rule_name):
        try:
            settings = [await self.get_rule_setting(guild, rule_name)]
            # convert to list
            return await self.get_settings_to_embeds(settings)
        except KeyError:
            return None

    @commands.group()
    @checks.mod_or_permissions(manage_messages=True)
    async def automodset(self, ctx):
        """
        Change automod settings.
        """
        pass

    @automodset.command(name="show", aliases=["all"])
    async def show_all_settings(self, ctx, rulename: str = None):
        """
        Show settings

        If rulename is not provided a formatted embed will show all rules and their status.

        For more granular details provide a rulename
        """
        if rulename is None:
            for embed in await self.get_all_settings_as_embeds(ctx.guild):
                await ctx.send(embed=embed)
        else:
            if rulename not in self.rules_map:
                nl = "\n"
                return await ctx.send(
                    await error_message(
                        f"`{rulename}` is not a valid rule. The options are:\n\n"
                        f"{nl.join('• `{0}`'.format(w) for w in self.rules_map)}"
                    )
                )
            embed = await self.get_rule_settings_as_embed(ctx.guild, rulename)
            await ctx.send(embed=embed[0])

    @automodset.group()
    @checks.mod_or_permissions(manage_messages=True)
    async def announce(self, ctx):
        """
        Message announcement settings
        """
        pass

    @announce.command(name="toggle")
    @checks.mod_or_permissions(manage_messages=True)
    async def _enable(self, ctx, toggle: ToggleBool=None):
        """
        Toggles sending announcement messages on infractions.


        """
        is_announcing, channel = await self.announcements_enabled(ctx.guild)
        if toggle is None:
            return await ctx.send(f"Announcing in this guild is `{transform_bool(is_announcing)}`.")

        if is_announcing == toggle:
            return await ctx.send(await error_message(f"Announcing is already `{transform_bool(is_announcing)}`"))

        before, after = await self.toggle_announcements(ctx.guild, toggle)

        log.info(f"{ctx.author} ({ctx.author.id}) toggled announcements from {before} to {after}")
        await ctx.send(
            f"`🔔` Announcements changed from `{transform_bool(before)}` to `{transform_bool(after)}`"
        )

    @announce.command()
    @checks.mod_or_permissions(manage_messages=True)
    async def channel(self, ctx, channel: discord.TextChannel):
        """
        Set the channel where announcements should be posted.

        """
        before, after = await self.set_announcement_channel(ctx.guild, channel)

        log.info(
            f"{ctx.author} ({ctx.author.id}) changed announcement channel from {before} to {after}"
        )
        await ctx.send(f"`🔔` Announcement channel changed from `{before}` to `{after}`")
