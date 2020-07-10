from os.path import splitext
from typing import Optional

import discord

from dataclasses import dataclass

from redbot.core.utils.chat_formatting import box

from .base import BaseRule
from .config.models import InfractionInformation, BlackOrWhiteList

WHITELIST_EXTENSIONS = "whitelist_extensions"
BLACKLIST_EXTENSIONS = "blacklist_extensions"


@dataclass
class ExtensionsAndChannels:
    extensions: [str]
    channels: [int]


def get_message_extensions(message: discord.Message) -> [str]:
    """Get a list of all attachment extensions in a message"""
    return [splitext(attachment.filename.lower())[1] for attachment in message.attachments]


class AllowedExtensionsRule(BaseRule):
    def __init__(self, config):
        super().__init__(config)

    async def _set_extensions(
        self,
        guild: discord.Guild,
        extensions: [str],
        channels: [discord.TextChannel],
        white_or_black_list: str,
    ):
        """
        Add extension(s) to the whitelist per channel
        Parameters
        ----------
        guild
            The guild where to add these extensions
        extensions
            The extension type
        channels
            The channels to apply this whitelist
        white_or_black_list
            The config KEY to use
        """
        to_append = {"extensions": extensions, "channels": [ch.id for ch in channels]}
        try:
            extensions = await self.config.guild(guild).get_raw(
                self.rule_name, white_or_black_list
            )
            extensions.append(to_append)
            await self.config.guild(guild).set_raw(
                self.rule_name, white_or_black_list, value=extensions
            )
        except KeyError:
            # none have been created yet
            await self.config.guild(guild).set_raw(
                self.rule_name, white_or_black_list, value=[to_append]
            )

    async def _get_extensions(
        self, guild: discord.Guild, white_or_black_list: str
    ) -> [ExtensionsAndChannels]:
        """
        Get's all currently whitelisted extensions
        Parameters
        ----------
        guild
            The guild to get extensions from
        white_or_black_list
            the config key to get 
        """
        try:
            extensions = await self.config.guild(guild).get_raw(
                self.rule_name, white_or_black_list
            )
            return [ExtensionsAndChannels(**c) for c in extensions]
        except KeyError:
            return None

    async def _delete_extensions(
        self, guild: discord.Guild, white_or_black_list: str, index: int
    ) -> ExtensionsAndChannels:
        extensions = await self.config.guild(guild).get_raw(self.rule_name, white_or_black_list)
        to_delete = extensions[index]
        extensions.remove(to_delete)
        await self.config.guild(guild).set_raw(
            self.rule_name, white_or_black_list, value=extensions
        )

        return ExtensionsAndChannels(**to_delete)

    async def set_whitelist_extensions(
        self, guild: discord.Guild, extensions: [str], channels: [discord.TextChannel]
    ):
        await self._set_extensions(guild, extensions, channels, WHITELIST_EXTENSIONS)

    async def get_whitelist_extensions(self, guild: discord.Guild) -> [ExtensionsAndChannels]:
        return await self._get_extensions(guild, WHITELIST_EXTENSIONS)

    async def delete_whitelist_extensions(self, guild: discord.Guild, index: int):
        return await self._delete_extensions(guild, WHITELIST_EXTENSIONS, index)

    async def delete_blacklist_extensions(self, guild: discord.Guild, index: int):
        return await self._delete_extensions(guild, BLACKLIST_EXTENSIONS, index)

    async def set_blacklist_extensions(
        self, guild: discord.Guild, extensions: [str], channels: [discord.TextChannel]
    ):
        await self._set_extensions(guild, extensions, channels, BLACKLIST_EXTENSIONS)

    async def get_blacklist_extensions(self, guild: discord.Guild) -> [ExtensionsAndChannels]:
        return await self._get_extensions(guild, BLACKLIST_EXTENSIONS)

    @staticmethod
    async def deleted_extensions_embed(guild: discord.Guild, extension: ExtensionsAndChannels):
        """Gets an embed for displaying deleted extensions"""
        nl = "\n"
        chans = box(
            nl.join("+ {0}".format(guild.get_channel(w)) for w in extension.channels)
            if extension.channels
            else "+ Global",
            "diff",
        )
        fmt_box = box(nl.join("+ {0}".format(ext) for ext in extension.extensions), "diff")
        embed = discord.Embed(color=discord.Color.red(), description="Extensions deleted.")
        embed.add_field(name="Channels", value=chans, inline=False)
        embed.add_field(name="Extensions", value=fmt_box, inline=False)

        return embed

    @staticmethod
    async def extension_added_embed(extensions, channels) -> discord.Embed:
        nl = "\n"
        chans = box(
            nl.join("+ {0}".format(w) for w in channels) if channels else "+ Global", "diff"
        )
        fmt_box = box(nl.join("+ {0}".format(ext) for ext in extensions), "diff")
        embed = discord.Embed(color=discord.Color.green(), description="Extensions added.")
        embed.add_field(name="Channels", value=chans, inline=False)
        embed.add_field(name="Extensions", value=fmt_box, inline=False)

        return embed

    @staticmethod
    async def is_blacklist(message_exts: [str], blacklisted_exts: [str]):
        for ext in message_exts:
            ext = ext.replace(".", "")
            if ext in blacklisted_exts:
                return ext

        return None

    @staticmethod
    async def is_whitelist(message_exts: [str], whitelisted_exts: [str]):
        for ext in message_exts:
            ext = ext.replace(".", "")
            if ext not in whitelisted_exts:
                return ext

        return None

    async def get_announcement_embed(
        self,
        message: discord.Message,
        message_has_been_deleted: bool,
        action_taken_success: bool,
        action_taken: Optional[str],
        infraction_information=None,
    ) -> discord.Embed:
        embed = await super().get_announcement_embed(
            message,
            message_has_been_deleted,
            action_taken_success,
            action_taken,
            infraction_information,
        )
        embed.description = infraction_information.embed_description
        return embed

    async def is_offensive(self, message: discord.Message):
        content, guild, attachments, channel = (
            message.content,
            message.guild,
            message.attachments,
            message.channel,
        )

        if not attachments:
            return

        message_attachment_extensions = get_message_extensions(message)

        # Blacklist takes precedent
        blacklist_extensions = await self.get_blacklist_extensions(guild)
        for entry in blacklist_extensions:
            if channel.id in entry.channels or entry.channels is None:
                blacklisted_extension = await self.is_blacklist(
                    message_attachment_extensions, entry.extensions
                )
                if blacklisted_extension:
                    return InfractionInformation(
                        message=content,
                        rule=self,
                        embed_description=f"Blacklisted extension found: `{blacklisted_extension}`",
                    )

        whitelist_extensions = await self.get_whitelist_extensions(guild)
        for entry in whitelist_extensions:
            if channel.id in entry.channels or entry.channels is None:
                whitelisted_extension = await self.is_whitelist(
                    message_attachment_extensions, entry.extensions
                )
                if whitelisted_extension:
                    return InfractionInformation(
                        message=content,
                        rule=self,
                        embed_description=f"Extension found not in allowed whitelist: `{whitelisted_extension}`",
                    )
