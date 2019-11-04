import discord
import logging

from redbot.core.commands import Cog
from redbot.core import Config, commands

from .rules.wallspam import WallSpamRule
from .rules.mentionspam import MentionSpamRule
from .rules.discordinvites import DiscordInviteRule
from .rules.spamrule import SpamRule
from .rules.maxchars import MaxCharsRule
from .rules.maxwords import MaxWordsRule

from .constants import *
from .groupcommands import GroupCommands

from .settings import Settings
from .utils import (
    transform_bool,
    get_option_reaction,
    thumbs_up_success,
    yes_or_no,
    maybe_add_role,
)

log = logging.getLogger(name="red.breadcogs.automod")

class AutoMod(Cog, Settings, GroupCommands):
    def __init__(self, bot, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=78945698745687, force_registration=True
        )


        self.guild_defaults = {
            "settings": {"announcement_channel": None, "is_announcement_enabled": True},
            WallSpamRule.__class__.__name__: DEFAULT_OPTIONS,
            MentionSpamRule.__class__.__name__: DEFAULT_OPTIONS,
            DiscordInviteRule.__class__.__name__: DEFAULT_OPTIONS,
        }

        self.config.register_guild(**self.guild_defaults)

        # rules
        self.wallspamrule = WallSpamRule(self.config)
        self.mentionspamrule = MentionSpamRule(self.config)
        self.inviterule = DiscordInviteRule(self.config)
        self.spamrule = SpamRule(self.config)
        self.maxwords = MaxWordsRule(self.config)
        self.maxchars = MaxCharsRule(self.config)

        self.rules_map = {
            "wallspam": self.wallspamrule,
            "mentionspam": self.mentionspamrule,
            "inviterule": self.inviterule,
            "spamrule": self.spamrule,
            "maxwords": self.maxwords,
            "maxchars": self.maxchars
        }

    async def _take_action(self, rule, message: discord.Message):
        guild: discord.Guild = message.guild
        author: discord.Member = message.author
        channel: discord.TextChannel = message.channel

        action_to_take = await rule.get_action_to_take(guild)
        self.bot.dispatch(f"automod_{rule.rule_name}", author, message)
        log.info(
            f"{rule.rule_name} - {author} ({author.id}) - {guild} ({guild.id}) - {channel} ({channel.id})"
        )

        _action_reason = f"[AutoMod] {rule.rule_name}"

        should_announce, announce_channel = await self.announcements_enabled(
            guild=guild
        )
        should_delete = await rule.get_should_delete(guild)

        message_has_been_deleted = False
        if should_delete:
            try:
                await message.delete()
                message_has_been_deleted = True
            except discord.errors.Forbidden:
                log.warning(f"[AutoMod] {rule.name} - Missing permissions to delete message")
            except discord.errors.NotFound:
                message_has_been_deleted = True
                log.warning(f"[AutoMod] {rule.name} - Could not delete message as it does not exist")

        if should_announce:
            if announce_channel is not None:
                announce_embed = await rule.get_announcement_embed(
                    message, message_has_been_deleted, action_to_take
                )
                announce_channel_obj = guild.get_channel(announce_channel)
                await announce_channel_obj.send(embed=announce_embed)

        if action_to_take == "third_party":
            # do nothing but we still fire the event
            # so other devs can hook onto custom mod cogs for example
            return

        elif action_to_take == "kick":
            try:
                await author.kick(reason=_action_reason)
                log.info(f"{rule.rule_name} - Kicked {author} ({author.id})")
            except discord.errors.Forbidden:
                log.warning(
                    f"{rule.rule_name} - Failed to kick user, missing permissions"
                )

        elif action_to_take == "add_role":
            try:
                role = guild.get_role(
                    await self.config.guild(guild).get_raw(
                        rule.rule_name, "role_to_add"
                    )
                )
                await maybe_add_role(author, role)
                log.info(
                    f"{rule.rule_name} - Added Role (role) to {author} ({author.id})"
                )
            except KeyError:
                # role to add not set
                log.info(f"{rule.rule_name} No role set to add to offending user")
                pass

        elif action_to_take == "ban":
            try:
                await guild.ban(
                    user=author, reason=_action_reason, delete_message_days=1
                )
                log.info(f"{rule.rule_name} - Banned {author} ({author.id})")
            except discord.errors.Forbidden:
                log.warning(
                    f"{rule.rule_name} - Failed to ban user, missing permissions"
                )
            except discord.errors.HTTPException:
                log.warning(f"{rule.rule_name} - Failed to ban user [HTTP EXCEPTION]")

    @Cog.listener(name="on_message_without_command")
    async def _listen_for_infractions(self, message: discord.Message):
        guild = message.guild
        author = message.author

        # DM's
        if not message.guild:
            return

        # immune from automod actions
        if await self.bot.is_automod_immune(message.author):
            return

        # don't listen to other bots, no skynet here
        if message.author.bot:
            return

        for rule_name, rule in self.rules_map.items():
            if await rule.is_enabled(guild):
                # check all if roles - if any are immune, then that's okay, we'll let them spam :)
                is_whitelisted_role = await rule.role_is_whitelisted(
                    guild, author.roles
                )
                if is_whitelisted_role:
                    # user is whitelisted, let's stop here
                    return

                if await rule.is_offensive(message):
                    await self._take_action(rule, message)
