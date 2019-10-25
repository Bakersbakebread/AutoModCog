import discord
from functools import partial
from redbot.core.commands import (
    Cog,
    command,
    group,
    check,
    CheckFailure,
    Converter,
    BadArgument,
)
from redbot.core import Config
import logging
from .constants import *

from .utils import transform_bool, get_option_reaction, thumbs_up_success, yes_or_no

from .rules.wallspam import WallSpamRule

from .constants import DEFAULT_OPTIONS

log = logging.getLogger(name="red.breadcogs.automod")


class AutoMod(Cog):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=78945698745687, force_registration=True
        )
        self.wallspam = WallSpamRule(self.config)
        self.guild_defaults = {WallSpamRule.__class__.__name__: DEFAULT_OPTIONS}
        self.config.register_guild(**self.guild_defaults)
        self.rules_map = {"wallspam": self.wallspam}
        self.rules_string = "\n".join([key for key in self.rules_map])

    async def is_a_rule(self, rule):
        try:
            return self.rules_map[rule]
        except:
            return None

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

        if action_to_take == "third_party":
            await channel.send("Would do nothing (Third Party)")
            return

        elif action_to_take == "kick":
            try:
                # await author.kick(reason=_action_reason)
                await channel.send("would kick user")
                log.info(f"{rule.rule_name} - Kicked {author} ({author.id})")
            except discord.errors.Forbidden:
                log.warning(
                    f"{rule.rule_name} - Failed to kick user, missing permissions"
                )

        elif action_to_take == "add_role":
            await message.channel.send("Would add role to user")
            log.info(f"{rule.rule_name} - Added Role (role) to {author} ({author.id})")

        elif action_to_take == "ban":
            await channel.send("Would ban user")
            # try:
            #     await guild.ban(user = author, reason = _action_reason, delete_message_days=1)
            #     log.info(f"{rule.rule_name} - Banned {author} ({author.id})")
            # except discord.errors.Forbidden:
            #     log.warning(f"{rule.rule_name} - Failed to ban user, missing permissions")
            # except discord.errors.HTTPException:
            #     log.warning(f"{rule.rule_name} - Failed to ban user [HTTP EXCEPTION]")

    @Cog.listener(name="on_automod_WallSpamRule")
    async def _do_stuff(self, author, message):
        print("did stuff")
        print(author)
        print(message)

    @Cog.listener(name="on_message")
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
            if not await rule.is_enabled(guild):
                return
            # check all if roles - if any are immune, then that's okay, we'll let them spam :)
            is_whitelisted_role = await rule.role_is_whitelisted(guild, author.roles)
            if is_whitelisted_role:
                # user is whitelisted, let's stop here
                return

            if await rule.is_offensive(message):
                await self._take_action(rule, message)

    @group()
    async def automod(self, ctx):
        """
        Base command for autmod settings.

        Available rules:
        **Wallspam** - Detects large repetitive wallspam
        """
        pass

    @automod.command()
    async def enable(self, ctx, rule_name):
        """
        Toggles wallspam automodding

        """
        rule = await self.is_a_rule(rule_name)
        if not rule:
            return await ctx.send(ERROR_MESSAGES["invalid_rule"].format(rule_name))
        before, after = await rule_name.toggle_enabled(ctx.guild)
        await ctx.send(
            f"**{rule_name.title()}** set from `{transform_bool(before)}` to `{transform_bool(after)}`"
        )

    @automod.command()
    async def action(self, ctx, rule_name):
        """
        Choose which action to take on an offensive wallspam message

       1) Nothing (still fires event for third-party integration)
       2) DM a role\n
       3) Add a role to offender (Mute role for example)
       4) Kick offender
       5) Ban offender
        """
        rule = await self.is_a_rule(rule_name)
        if not rule:
            return await ctx.send(ERROR_MESSAGES["invalid_rule"].format(rule_name))
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

    @automod.command()
    async def delete(self, ctx, rule_name):
        """
        Toggles whether message should be deleted on offence

        `manage_messages` perms are needed for this to run.
        """
        rule = await self.is_a_rule(rule_name)
        if not rule:
            return await ctx.send(ERROR_MESSAGES["invalid_rule"].format(rule_name))
        before, after = await rule.toggle_to_delete_message(ctx.guild)
        await ctx.send(
            f"Deleting messages set from `{transform_bool(before)}` to `{transform_bool(after)}`"
        )

    @automod.command()
    async def message(self, ctx, rule_name):
        """"
        Toggles whether to send a Private Message to the user.

        This method will fail silently.
        """
        rule = await self.is_a_rule(rule_name)
        if not rule:
            return await ctx.send(ERROR_MESSAGES["invalid_rule"].format(rule_name))

    @automod.command()
    async def whitelistrole(self, ctx, rule_name, role: discord.Role):
        rule = await self.is_a_rule(rule_name)
        if not rule:
            return await ctx.send(ERROR_MESSAGES["invalid_rule"].format(rule_name))
        try:
            await rule.append_whitelist_role(ctx.guild, role)
        except ValueError:
            await ctx.send(f"`{role}` is already whitelisted.", delete_after=30)
            result = await yes_or_no(
                ctx, f"Would you like to remove `{role}` from the whitelist?"
            )
            if result:
                await rule.remove_whitelist_role(ctx.guild, role)
        await ctx.send("Done")

    @automod.command()
    async def role(self, ctx, rule_name, role: discord.Role):
        """
        Set the role to add to offender

        When a rule offence is found and action to take is set to "Add Role", this role is the one that will be added.
        """
        rule = await self.is_a_rule(rule_name)
        if not rule:
            return await ctx.send(ERROR_MESSAGES["invalid_rule"].format(rule_name))

        before, after = await rule.set_mute_role(ctx.guild, role)

        await ctx.send(
            f"Role to add set from `{before}` to `{after}`"
        )
