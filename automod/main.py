import discord
import logging

from redbot.core.commands import Cog
from redbot.core import Config, commands

from .rules.wallspam import WallSpamRule
from .rules.mentionspam import MentionSpamRule
from .rules.discordinvites import DiscordInviteRule

from .constants import *

from .settings import Settings
from .utils import (
    transform_bool,
    get_option_reaction,
    thumbs_up_success,
    yes_or_no,
    maybe_add_role,
)

log = logging.getLogger(name="red.breadcogs.automod")

groups = {
    "mentionspamrule": "Mention spam",
    "wallspamrule": "Wall spam",
    "inviterule": "Discord invites",
}

# thanks Jackenmen#6607 <3


class GroupCommands:
    # commands specific to mention spam rule
    @commands.group()
    async def mentionspamrule(self, ctx):
        """Individual mentions spam settings"""
        pass

    @mentionspamrule.command()
    async def threshold(self, ctx, threshold: int):
        """Set the max amount of individual mentions allowed

        This overrides the default number of 4 individual mentions on the Mention Spam rule
        """
        before, after = await self.mentionspamrule.set_threshold(ctx, threshold)
        await ctx.send(f"`🎯` Mention threshold changed from `{before}` to `{after}`")

    # commands specific to wall spam rule
    @commands.group()
    async def wallspamrule(self, ctx):
        """Walls of text/emojis settings"""
        pass

    # commands specific to discord invite rule
    @commands.group()
    async def inviterule(self, ctx):
        """Filters discord invites

        Supported type of discord links:
        `discord.gg/inviteCode`
        `discordapp.com/invite/inviteCode`
        """
        pass

    @inviterule.group()
    async def whitelistlink(self, ctx):
        """Add/remove/show links allowed

        Adding a link to the whitelist will allow it to be immune from automod actions"""
        pass

    @whitelistlink.command(name="add")
    async def add_link(self, ctx, link: str):
        """
        Add a link to not be filtered.

        This must be the full link, supported types:

        discord.gg/inviteCode
        discordapp.com/invite/inviteCode
        """
        try:
            await self.inviterule.add_allowed_link(ctx.guild, link)
        except ValueError:
            return await ctx.send("`👆` That link already exists.")

        return await ctx.send(f"`👍` Added `{link}` to the allowed links list.")

    @whitelistlink.command(name="delete")
    async def delete_link(self, ctx, link: str):
        """
        Deletes a link from the ignore list

        This must be the full exact match of a link in the list.
        """
        try:
            await self.inviterule.delete_allowed_link(ctx.guild, link)
        except ValueError as e:
            await ctx.send(f"`❌` {e.args[0]}")

    @whitelistlink.command(name="show")
    async def show_links(self, ctx):
        """
        Show a list of links that are not filtered.
        """
        allowed_links = await self.inviterule.get_allowed_links(ctx.guild)
        if allowed_links is not None:
            embed = discord.Embed(
                title="Links that are not filtered by the rule",
                description=", ".join("`{0}`".format(w) for w in allowed_links),
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"`❌` No links currently allowed.")


def enable_rule_wrapper(group, name, friendly_name):
    @group.command(name="toggle")
    async def enable_rule(self, ctx):
        """
        Toggle enabling/disabling this rule

        """
        rule = getattr(self, name)
        before, after = await rule.toggle_enabled(ctx.guild)
        await ctx.send(
            f"**{friendly_name.title()}** set from `{transform_bool(before)}` to `{transform_bool(after)}`"
        )

    return enable_rule


def action_to_take__wrapper(group, name, friendly_name):
    @group.command(name="action")
    async def action_to_take(self, ctx):
        """
        Choose which action to take on an offensive message

       1) Nothing (still fires event for third-party integration)
       2) DM a role\n
       3) Add a role to offender (Mute role for example)
       4) Kick offender
       5) Ban offender
        """
        rule = getattr(self, name)
        embed = discord.Embed(
            title="What action should be taken against wallspam?",
            description=f":one: Nothing (still fires event for third-party integration)\n"
            f":two: DM a role\n"
            f":three: Add a role to offender (Mute role for example)\n"
            f":four: Kick offender\n"
            f":five: Ban offender",
        )
        action = await get_option_reaction(ctx, embed=embed)
        if action:
            await ctx.send(await thumbs_up_success(ACTION_CONFIRMATION[action]))
            await rule.set_action_to_take(action, ctx.guild)
        else:
            await ctx.send("Okay, nothing's changed.")

    return action_to_take


def delete_message_wrapper(group, name, friendly_name):
    @group.command(name="delete")
    async def delete_message(self, ctx):
        """
        Toggles whether message should be deleted on offence

        `manage_messages` perms are needed for this to run.
        """
        rule = getattr(self, name)
        before, after = await rule.toggle_to_delete_message(ctx.guild)
        await ctx.send(
            f"Deleting messages set from `{transform_bool(before)}` to `{transform_bool(after)}`"
        )

    return delete_message


def private_message_wrapper(group, name, friendly_name):
    @group.command(name="message")
    async def private_message(self, ctx):
        """
        Toggles whether to send a Private Message to the user.

        This method will fail silently.
        """
        rule = getattr(self, name)
        return await ctx.send("This setting is a WIP")

    return private_message


def whitelist_wrapper(group, name, friendly_name):
    @group.group(name="whitelistrole")
    async def whitelistrole(self, ctx):
        """Whitelisting roles settings

        Adding a role to the whitelist means that this role will be immune to automod actions
        """
        pass

    return whitelistrole


def whitelistrole_add_wrapper(group, name, friendly_name):
    @group.command(name="add")
    async def whitelistrole_add(self, ctx, role: discord.Role):
        """
                Add a role to be ignored by automod actions"

                Passing a role already whitelisted will prompt for deletion
                """
        rule = getattr(self, name)
        try:
            await rule.append_whitelist_role(ctx.guild, role)
        except ValueError:
            await ctx.send(f"`{role}` is already whitelisted.", delete_after=30)
            result = await yes_or_no(
                ctx, f"Would you like to remove `{role}` from the whitelist?"
            )
            if result:
                await rule.remove_whitelist_role(ctx.guild, role)
        await ctx.send(f"`{role}` added to the whitelist.")

    return whitelistrole_add


def whitelistrole_delete_wrapper(group, name, friendly_name):
    @group.command(name="delete")
    async def whitelistrole_delete(self, ctx, role: discord.Role):
        """Delete a role from being ignored by automod actions"""
        rule = getattr(self, name)
        try:
            await rule.remove_whitelist_role(ctx.guild, role)
        except ValueError:
            return await ctx.send(f"`{role}` is not whitelisted.")

    return whitelistrole_delete


def whitelistrole_show_wrapper(group, name, friendly_name):
    @group.command(name="show")
    async def whitelistrole_show(self, ctx):
        """Show all whitelisted roles"""
        rule = getattr(self, name)
        all_roles = await rule.get_all_whitelisted_roles(ctx.guild)
        if all_roles:
            desc = ", ".join("`{0}`".format(role) for role in all_roles)
            em = discord.Embed(
                title="Whitelisted roles",
                description=desc,
                color=discord.Color.greyple(),
            )
            await ctx.send(embed=em)
        else:
            await ctx.send("`❌` No roles currently whitelisted.")

    return whitelistrole_show


def add_role_wrapper(group, name, friendly_name):
    @group.command(name="role")
    async def add_role(self, ctx, role: discord.Role):
        """
        Set the role to add to offender

        When a rule offence is found and action to take is set to "Add Role", this role is the one that will be added.
        """
        rule = getattr(self, name)
        before, after = await rule.set_mute_role(ctx.guild, role)

        await ctx.send(f"Role to add set from `{before}` to `{after}`")

    return add_role


for name, friendly_name in groups.items():
    group = getattr(GroupCommands, name)

    enable_rule = enable_rule_wrapper(group, name, friendly_name)
    enable_rule.__name__ = f"enable_{name}"
    setattr(GroupCommands, f"enable_{name}", enable_rule)

    action_to_take = action_to_take__wrapper(group, name, friendly_name)
    action_to_take.__name__ = f"action_{name}"
    setattr(GroupCommands, f"action_{name}", action_to_take)

    delete_message = delete_message_wrapper(group, name, friendly_name)
    delete_message.__name__ = f"delete_{name}"
    setattr(GroupCommands, f"delete_{name}", delete_message)

    private_message = private_message_wrapper(group, name, friendly_name)
    private_message.__name__ = f"private_message_{name}"
    setattr(GroupCommands, f"private_message_{name}", private_message)

    # whitelist settings
    # whitelist commands inherit whitelist role group
    whitelistrole = whitelist_wrapper(group, name, friendly_name)
    whitelistrole.__name__ = f"whitelistrole_{name}"
    setattr(GroupCommands, f"whitelistrole_{name}", whitelistrole)

    # whitelist group
    whitelistrole_delete = whitelistrole_delete_wrapper(
        whitelistrole, name, friendly_name
    )
    whitelistrole_delete.__name__ = f"whitelistrole_delete_{name}"
    setattr(GroupCommands, f"whitelistrole_delete_{name}", whitelistrole_delete)

    # whitelist group
    whitelistrole_add = whitelistrole_add_wrapper(whitelistrole, name, friendly_name)
    whitelistrole_add.__name__ = f"whitelistrole_add_{name}"
    setattr(GroupCommands, f"whitelistrole_add_{name}", whitelistrole_add)

    # whitelist group
    whitelistrole_show = whitelistrole_show_wrapper(whitelistrole, name, friendly_name)
    whitelistrole_show.__name__ = f"whitelistrole_show_{name}"
    setattr(GroupCommands, f"whitelistrole_show_{name}", whitelistrole_show)

    add_role = add_role_wrapper(group, name, friendly_name)
    add_role.__name__ = f"add_role_{name}"
    setattr(GroupCommands, f"add_role_{name}", add_role)


class AutoMod(Cog, Settings, GroupCommands):
    def __init__(self, bot, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=78945698745687, force_registration=True
        )
        # rules
        self.wallspamrule = WallSpamRule(self.config)
        self.mentionspamrule = MentionSpamRule(self.config)
        self.inviterule = DiscordInviteRule(self.config)

        self.guild_defaults = {
            "settings": {"announcement_channel": None, "is_announcement_enabled": True},
            WallSpamRule.__class__.__name__: DEFAULT_OPTIONS,
            MentionSpamRule.__class__.__name__: DEFAULT_OPTIONS,
            DiscordInviteRule.__class__.__name__: DEFAULT_OPTIONS,
        }

        self.config.register_guild(**self.guild_defaults)
        self.rules_map = {
            "wallspam": self.wallspamrule,
            "mentionspam": self.mentionspamrule,
            "inviterule": self.inviterule,
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

        if should_delete:
            try:
                await message.delete()
            except discord.errors.Forbidden:
                log.warning("Missing permissions to delete message")

        if should_announce:
            if announce_channel is not None:
                announce_embed = await rule.get_announcement_embed(
                    message, action_to_take
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
