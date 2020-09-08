# date | month | year
__version__ = "08.09.2020"
__author__ = ("Bread#0007", 280730525960896513)
__credits__ = ["xBlynd"]
__status__ = "Production"

import dataclasses

import discord
import logging

from redbot.core.commands import Cog
from redbot.core import Config
from redbot.core.data_manager import bundled_data_path

from .rules.allowedextensions import AllowedExtensionsRule

from .rules.config.models import InfractionInformation
from .rules.imagedetection import ImageDetectionRule
from .rules.wordfilter import WordFilterRule
from .rules.wallspam import WallSpamRule
from .rules.mentionspam import MentionSpamRule
from .rules.discordinvites import DiscordInviteRule
from .rules.spamrule import SpamRule
from .rules.maxchars import MaxCharsRule
from .rules.maxwords import MaxWordsRule

from .constants import *
from .groupcommands import GroupCommands

from .settings import Settings
from .utils import maybe_add_role

log = logging.getLogger(name="red.breadcogs.automod")


class AutoMod(
    Cog, Settings, GroupCommands,
):
    def __init__(
        self, bot, *args, **kwargs,
    ):

        super().__init__(
            *args, **kwargs,
        )
        self.bot = bot
        self.config = Config.get_conf(self, identifier=78945698745687, force_registration=True,)

        self.guild_defaults = {
            "settings": {"announcement_channel": None, "is_announcement_enabled": False,},
            WallSpamRule.__class__.__name__: DEFAULT_OPTIONS,
            MentionSpamRule.__class__.__name__: DEFAULT_OPTIONS,
            DiscordInviteRule.__class__.__name__: DEFAULT_OPTIONS,
            SpamRule.__class__.__name__: DEFAULT_OPTIONS,
            MaxWordsRule.__class__.__name__: DEFAULT_OPTIONS,
            MaxCharsRule.__class__.__name__: DEFAULT_OPTIONS,
            WordFilterRule.__class__.__name__: DEFAULT_OPTIONS,
            ImageDetectionRule.__class__.__name__: DEFAULT_OPTIONS,
        }

        self.config.register_guild(**self.guild_defaults)
        self.data_path = bundled_data_path(self)

        # rules
        self.wallspamrule = WallSpamRule(self.config)
        self.mentionspamrule = MentionSpamRule(self.config)
        self.inviterule = DiscordInviteRule(self.config)
        self.spamrule = SpamRule(self.config, self.bot, self.data_path)
        self.maxwordsrule = MaxWordsRule(self.config)
        self.maxcharsrule = MaxCharsRule(self.config)
        self.wordfilterrule = WordFilterRule(self.config)
        self.imagedetectionrule = ImageDetectionRule(self.config)
        self.allowedextensionsrule = AllowedExtensionsRule(self.config)

        self.rules_map = {
            "wallspamrule": self.wallspamrule,
            "mentionspamrule": self.mentionspamrule,
            "inviterule": self.inviterule,
            "spamrule": self.spamrule,
            "maxwordsrule": self.maxwordsrule,
            "maxcharsrule": self.maxcharsrule,
            "wordfilterrule": self.wordfilterrule,
            "imagedetectionrule": self.imagedetectionrule,
            "allowedextensionsrule": self.allowedextensionsrule,
        }

    async def _take_action(
        self, rule, message: discord.Message, is_offensive: InfractionInformation = None
    ):
        guild: discord.Guild = message.guild
        author: discord.Member = message.author
        channel: discord.TextChannel = message.channel

        action_to_take = await rule.get_action_to_take(guild)
        self.bot.dispatch(f"automod_{rule.rule_name}", author, message)
        self.bot.dispatch(
            f"bread_automod",
            rule.rule_name,
            author,
            message,
            dataclasses.asdict(is_offensive) if is_offensive else None,
        )
        log.info(
            f"{rule.rule_name} - {author} ({author.id}) - {guild} ({guild.id}) - {channel} ({channel.id})"
        )

        _action_reason = f"[AutoMod] {rule.rule_name}"

        should_delete = await rule.get_should_delete(guild)
        message_has_been_deleted = False
        if should_delete:
            try:
                await message.delete()
                message_has_been_deleted = True
            except discord.errors.Forbidden:
                log.warning(f"[AutoMod] {rule.rule_name} - Missing permissions to delete message")
            except discord.errors.NotFound:
                message_has_been_deleted = True
                log.warning(
                    f"[AutoMod] {rule.rule_name} - Could not delete message as it does not exist"
                )
        action_taken_success = True
        if action_to_take == "kick":
            try:
                await author.kick(reason=_action_reason)
                log.info(f"{rule.rule_name} - Kicked {author} ({author.id})")
            except discord.errors.Forbidden:
                log.warning(f"{rule.rule_name} - Failed to kick user, missing permissions")
                action_taken_success = False

        elif action_to_take == "add_role":
            try:
                role = guild.get_role(
                    await self.config.guild(guild).get_raw(rule.rule_name, "role_to_add",)
                )
                await maybe_add_role(
                    author, role,
                )
                log.info(f"{rule.rule_name} - Added Role (role) to {author} ({author.id})")
            except KeyError:
                # role to add not set
                log.info(f"{rule.rule_name} No role set to add to offending user")
                action_taken_success = False

        elif action_to_take == "ban":
            try:
                await guild.ban(
                    user=author, reason=_action_reason, delete_message_days=1,
                )
                log.info(f"{rule.rule_name} - Banned {author} ({author.id})")
            except discord.errors.Forbidden:
                log.warning(f"{rule.rule_name} - Failed to ban user, missing permissions")
                action_taken_success = False
            except discord.errors.HTTPException:
                log.warning(f"{rule.rule_name} - Failed to ban user [HTTP EXCEPTION]")
                action_taken_success = False

        announce_embed = await rule.get_announcement_embed(
            message, message_has_been_deleted, action_taken_success, action_to_take, is_offensive,
        )
        await self.maybe_send_announcement(guild, rule, announce_embed)

    async def maybe_send_announcement(
        self, guild: discord.Guild, rule, announce_embed: discord.Embed
    ) -> None:
        """
        Method to send announcements to channel depending on settings. Can be local to the rule, or global.
        Parameters
        ----------
        guild
            The guild where infraction was found.
        rule
            The rule triggered.
        announce_embed
            Announcement embed
        """
        try:
            announce_channel = None

            should_announce_global, announce_channel_id = await self.announcements_enabled(
                guild=guild
            )
            if should_announce_global and announce_channel_id is not None:
                announce_channel = guild.get_channel(announce_channel_id)

            rule_specific_announce_channel = await rule.get_specific_announce_channel(guild)
            if rule_specific_announce_channel is not None:
                announce_channel = rule_specific_announce_channel

            if announce_channel is None:
                return  # not Announcing

            return await announce_channel.send(embed=announce_embed)
        except discord.errors.Forbidden:
            log.exception(f"Missing permissions to send messages")
        except discord.errors.NotFound:
            log.exception(f"Could not send announce embed as channel was deleted")

    @Cog.listener()
    async def on_message_edit(
        self, before: discord.Message, after: discord.Message,
    ):
        await self._listen_for_infractions(after)

    @Cog.listener(name="on_message_without_command")
    async def _listen_for_infractions(
        self, message: discord.Message,
    ):
        guild = message.guild
        author = message.author

        if __status__ == "Development":
            bread, bread_id = __author__
            if author.id != bread_id:
                return

        if not message.guild:
            return

        # immune from automod actions
        if isinstance(author, discord.Member) and await self.bot.is_automod_immune(message.author):
            return

        # don't listen to other bots, no skynet here
        if message.author.bot:
            return

        for (rule_name, rule,) in self.rules_map.items():
            if await rule.is_enabled(guild):
                # check all if roles - if any are immune, then that's okay, we'll let them spam :)
                is_whitelisted_role = await rule.role_is_whitelisted(guild, author.roles,)
                is_channel_or_global = await rule.is_enforced_channel(guild, message.channel,)
                if is_whitelisted_role or not is_channel_or_global:
                    # user is whitelisted, channel is not whitelisted let's stop here
                    return

                is_offensive = await rule.is_offensive(message)
                if is_offensive:
                    if isinstance(is_offensive, InfractionInformation):
                        await self._take_action(rule, message, is_offensive)
                    else:
                        await self._take_action(rule, message)
