from dataclasses import dataclass
from typing import Optional, Union

import discord
from abc import (
    ABC,
    abstractmethod,
)
from datetime import datetime

from ..converters import ToggleBool
from ..constants import (
    DEFAULT_ACTION,
    DEFAULT_OPTIONS,
    OPTIONS_MAP,
)
from async_lru import alru_cache
import timeit


@dataclass()
class BaseRuleSettingsDisplay:
    rule_name: str
    guild_id: int
    is_enabled: bool
    action_to_take: str
    is_deleting: bool
    enforced_channels: Optional[list]
    whitelisted_roles: Optional[list]
    muted_role: Optional[str]


class BaseRule:
    def __init__(self, config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.rule_name = self.__class__.__name__

    @abstractmethod
    async def is_offensive(self, message: discord.Message):
        pass

    async def get_settings(self, guild: discord.Guild,) -> BaseRuleSettingsDisplay:
        return BaseRuleSettingsDisplay(
            rule_name=self.rule_name,
            guild_id=guild.id,
            is_enabled=await self.is_enabled(guild),
            action_to_take=await self.get_action_to_take(guild),
            is_deleting=await self.get_should_delete(guild),
            enforced_channels=await self.get_enforced_channels(guild),
            whitelisted_roles=await self.get_all_whitelisted_roles(guild),
            muted_role=await self.get_mute_role(guild),
        )

    async def _clear_cache(self, func):
        """Function helper to clear cache"""
        try:
            await func.cache_clear()
        except TypeError:
            # cache probably cleared already
            pass

    # enabling
    @alru_cache(maxsize=32)
    async def is_enabled(self, guild: discord.Guild,) -> bool:
        """Helper to return the status of Rule"""
        try:
            return await self.config.guild(guild).get_raw(self.rule_name, "is_enabled",)
        except KeyError:
            return False

    async def toggle_enabled(self, guild: discord.Guild, toggle: ToggleBool) -> (bool, bool):
        """Toggles whether the rule is in effect"""
        await self._clear_cache(self.is_enabled)
        before = False
        try:
            before = await self.config.guild(guild).get_raw(self.rule_name, "is_enabled")
        except KeyError:
            pass

        await self.config.guild(guild).set_raw(self.rule_name, "is_enabled", value=toggle)

        return before, toggle

    async def set_enforced_channels(self, guild: discord.Guild, channels: [discord.TextChannel]):
        """Setting a channel will disable global"""
        await self._clear_cache(self.get_enforced_channels)

        config_channels = []

        for channel in channels:
            if channel.id not in config_channels:
                config_channels.append(channel.id)

        await self.config.guild(guild).set_raw(
            self.rule_name, "enforced_channels", value=config_channels
        )
        return config_channels

    @alru_cache(maxsize=32)
    async def get_enforced_channels(self, guild: discord.Guild,) -> [discord.TextChannel]:
        """Returns enabled channels, empty list if none set"""

        channels = []
        try:
            channels = await self.config.guild(guild).get_raw(self.rule_name, "enforced_channels",)
        except KeyError:
            pass

        return channels

    async def is_enforced_channel(
        self, guild: discord.Guild, channel: discord.TextChannel,
    ):
        enforced_channels = await self.get_enforced_channels(guild)
        # global
        if not enforced_channels:
            return True

        if channel.id in enforced_channels:
            return True

        return False

    # announcing
    @alru_cache(maxsize=32)
    async def get_specific_announce_channel(
        self, guild: discord.Guild
    ) -> Union[discord.TextChannel, None]:
        try:
            channel_id = await self.config.guild(guild).get_raw(
                self.rule_name, "rule_specific_announce"
            )
            return guild.get_channel(channel_id)
        except KeyError:
            # not set, so is disabled
            return None

    async def set_specific_announce_channel(
        self, guild: discord.Guild, channel: discord.TextChannel
    ) -> None:
        """Stores the channel ID inside of config"""
        await self._clear_cache(self.get_specific_announce_channel)
        print(channel)
        await self.config.guild(guild).set_raw(
            self.rule_name, "rule_specific_announce", value=channel.id
        )

    async def clear_specific_announce_channel(self, guild: discord.Guild):
        await self._clear_cache(self.get_specific_announce_channel)
        await self.config.guild(guild).set_raw(
            self.rule_name, "rule_specific_announce", value=None
        )

    # actions
    @alru_cache(maxsize=32)
    async def get_action_to_take(self, guild: discord.Guild,) -> str:
        """Helper to return what action is currently set on offence"""
        try:
            return await self.config.guild(guild).get_raw(self.rule_name, "action_to_take",)
        except KeyError:
            await self.config.guild(guild).set_raw(
                self.rule_name, "action_to_take", value=DEFAULT_ACTION,
            )
            return DEFAULT_ACTION

    async def set_action_to_take(
        self, action: str, guild: discord.Guild,
    ):
        """Sets the action to take on an offence"""
        try:
            await self.get_action_to_take.cache_clear()
        except TypeError:
            # cache probably not exists or clear already
            pass
        await self.config.guild(guild).set_raw(
            self.rule_name, "action_to_take", value=action,
        )

    @alru_cache(maxsize=32)
    async def get_should_delete(self, guild: discord.Guild):
        try:
            return await self.config.guild(guild).get_raw(self.rule_name, "delete_message",)
        except KeyError:
            return False

    async def toggle_to_delete_message(self, guild: discord.Guild) -> (bool, bool):
        """Toggles whether offending message should be deleted"""
        await self._clear_cache(self.get_should_delete)
        try:
            before = await self.config.guild(guild).get_raw(self.rule_name, "delete_message")
        except KeyError:
            before = True
        await self.config.guild(guild).set_raw(
            self.rule_name, "delete_message", value=not before,
        )

        return before, not before

    async def role_is_whitelisted(self, guild: discord.Guild, roles: [discord.Role],) -> bool:
        """Checks if role is whitelisted"""
        try:
            whitelist_roles = await self.config.guild(guild).get_raw(
                self.rule_name, "whitelist_roles"
            )
        except KeyError:
            # no roles are whitelisted
            return False

        # return any(role in whitelist_roles for role in [role.id for role in roles])
        for role in roles:
            if role.id in whitelist_roles:
                return True
        return False

    async def append_whitelist_role(self, guild: discord.Guild, role: discord.Role):
        """Adds role to whitelist"""
        await self._clear_cache(self.get_all_whitelisted_roles)
        try:
            roles = await self.config.guild(guild).get_raw(self.rule_name, "whitelist_roles",)
            if role.id in roles:
                raise ValueError("Role is already whitelisted")

            roles.append(role.id)
            await self.config.guild(guild).set_raw(
                self.rule_name, "whitelist_roles", value=roles,
            )

        except KeyError:
            # no roles added yet
            return await self.config.guild(guild).set_raw(
                self.rule_name, "whitelist_roles", value=[role.id],
            )

    async def remove_whitelist_role(self, guild: discord.Guild, role: discord.Role):
        """Removes role from whitelist"""
        await self._clear_cache(self.get_all_whitelisted_roles)
        roles = await self.config.guild(guild).get_raw(self.rule_name, "whitelist_roles",)
        if not role.id in roles:
            raise ValueError("That role is not whitelisted")

        roles.remove(role.id)

        await self.config.guild(guild).set_raw(
            self.rule_name, "whitelist_roles", value=roles,
        )

    @alru_cache(maxsize=32)
    async def get_all_whitelisted_roles(self, guild: discord.Guild):
        try:
            roles = await self.config.guild(guild).get_raw(self.rule_name, "whitelist_roles")
        except KeyError:
            # no roles added
            return None
        return roles

    async def toggle_sending_message(self, guild: discord.Guild) -> (bool, bool):
        try:
            before = await self.config.guild(guild).get_raw(self.rule_name, "send_dm")
        except KeyError:
            before = await self.config.guild(guild).set_raw(
                self.rule_name, "send_dm", value=DEFAULT_OPTIONS["send_dm"],
            )

        await self.config.guild(guild).set_raw(
            self.rule_name, "send_dm", value=(not before),
        )
        return before, not before

    async def get_mute_role(self, guild: discord.Guild,) -> str or None:
        try:
            return await self.config.guild(guild).get_raw(self.rule_name, "role_to_add",)
        except KeyError:
            return None

    async def set_mute_role(self, guild: discord.Guild, role: discord.Role,) -> tuple:

        before = None
        try:
            before = await self.config.guild(guild).get_raw(self.rule_name, "role_to_add",)
        except KeyError:
            # role not set yet probably
            pass

        await self.config.guild(guild).set_raw(
            self.rule_name, "role_to_add", value=role.id,
        )

        before_role = None
        if before:
            before_role = guild.get_role(before)

        after_role = guild.get_role(
            await self.config.guild(guild).get_raw(self.rule_name, "role_to_add")
        )

        return before_role, after_role

    @abstractmethod
    async def get_announcement_embed(
        self,
        message: discord.Message,
        message_has_been_deleted: bool,
        action_taken_success: bool,
        action_taken: Optional[str],
        infraction_information=None,
    ) -> discord.Embed:
        shortened_message_content = (
            (message.content[:120] + " .... (shortened)")
            if len(message.content.split()) > 25
            else message.content
        )

        embed = discord.Embed(
            title=f"{self.rule_name} - Offense found",
            description=f"```{shortened_message_content}```",
            color=discord.Color.gold(),
        )

        embed.add_field(
            name="Channel", value=f"{message.channel.mention}",
        )
        if action_taken:
            val = f"`{action_taken}`"
            if not action_taken_success:
                val += "\nFailed to take action. Check logs."
            embed.add_field(
                name="Action Taken", value=val,
            )
        embed.set_author(
            name=f"{message.author} - {message.author.id}", icon_url=message.author.avatar_url,
        )
        embed.timestamp = datetime.now()
        # embed.set_image(
        #     url=f"https://dummyimage.com/200x50/f31e13/ffffff.png&text={self.rule_name.replace('Rule', '')}"
        # )

        if not message_has_been_deleted:
            embed.add_field(
                name="Message status",
                value=f"`❌` Message has **not** been deleted - [🔗 Jump to message]({message.jump_url})",
                inline=False,
            )
        else:
            embed.add_field(
                name="Message status", value=f"`✅` Message has been deleted.", inline=False,
            )
        return embed

    async def get_settings_embed(
        self, guild: discord.Guild,
    ):
        """Returns a settings embed"""
        is_enabled = await self.config.guild(guild).get_raw(self.rule_name)
        desc = ""
        for (k, v,) in is_enabled.items():
            desc += f"**{OPTIONS_MAP[k]}** - `{v}`\n"
        embed = discord.Embed(title=f"{self.rule_name} settings", description=desc,)

        return embed
